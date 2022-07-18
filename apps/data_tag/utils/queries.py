from typing import List

from apps.data_tag.models import DataTag
from apps.storage.models import DataInfo
from apps.tag.models import Tag
from apps.tag.util.validator import tag_validator
from architecture.query.crud import QueryCRUD, QueryCreator, QueryReader
from core.exc import DataNotFound
from system.connection.generators import DatabaseGenerator


class DataTagQueryCreator(QueryCreator):
    def __call__(self, data_id: int, tags: List[str]):
        session = DatabaseGenerator.get_session()

        data_info = session.query(DataInfo) \
            .filter(DataInfo.id == data_id).scalar()
        if not data_info:
            raise DataNotFound()
        
        # Check Validate of tags
        tag_set = set()
        for tag in tags:
            if not tag_validator(tag):
                raise ValueError('Tag validate failed')
            if tag in tag_set:
                # 동일한 이름의 태그는 무시
                continue
            tag_set.add(tag)

        # 기존의 저장된 태그 불러오기
        cur_tags = session.query(DataTag, Tag) \
            .filter(DataTag.datainfo_id == data_id) \
            .filter(DataTag.id == Tag.id).all()

        # 기존의 태그 정보 임시저장
        # key: tagname, value (tag id, data_tag id)
        cur_tag_memory = dict()
        for data_tag, tag in cur_tags:
            cur_tag_memory[tag.name] = {
                'tag_id': tag.id, 'datatag_id': data_tag.id
            }

        # 태그 정보 갱신
        tag_set = list(tag_set)
        while tag_set:
            tag_name = tag_set.pop()
            if tag_name not in cur_tag_memory:
                # 없는 경우, 새로 생성한다.
                tag = Tag(name=tag_name)
                session.add(tag)
                session.commit()
                session.refresh(tag)

                data_tag = DataTag(datainfo_id=data_id, tag_id=tag.id)
                session.add(data_tag)
                session.commit()
            else:
                del cur_tag_memory[tag_name]

        # cur_tag_memory에 남아있는 애들은 삭제 대상이다.
        removed_tag_ids, removed_data_tag_ids = [], []
        for tag_info in cur_tag_memory.values():
            removed_tag_ids.append(tag_info['tag_id'])
            removed_data_tag_ids.append(tag_info['datatag_id'])

        # 삭제 수행
        session.query(DataTag) \
            .filter(DataTag.id.in_(removed_data_tag_ids)).delete()
        session.query(Tag) \
            .filter(Tag.id.in_(removed_tag_ids)).delete()
        session.commit()

        # 태그 데이터 다시 가져오기
        res = session.query(DataTag, Tag) \
            .filter(DataTag.datainfo_id == data_id) \
            .filter(DataTag.id == Tag.id) \
            .order_by(Tag.name).all()

        return [tag for _, tag in res]

class DataTagQueryReader(QueryReader):
    def __call__(self, data_id: int):
        session = DatabaseGenerator.get_session()
        
        data_info = session.query(DataInfo) \
            .filter(DataInfo.id == data_id).scalar()
        if not data_info:
            raise DataNotFound()
        
        res = session.query(DataTag, Tag) \
            .filter(DataTag.datainfo_id == data_id) \
            .filter(DataTag.id == Tag.id) \
            .order_by(Tag.name).all()

        return [tag for _, tag in res]


class DataTagQuery(QueryCRUD):
    creator = DataTagQueryCreator
    reader = DataTagQueryReader
