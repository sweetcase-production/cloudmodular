from architecture.query.permission import PermissionIssueChecker, PermissionUserLevelChecker


class PermissionIssueLoginChecker(PermissionIssueChecker):
    ref_v = 'logined'


class PermissionClientChecker(PermissionUserLevelChecker):
    ref_v = False # False -> 일반 사용자


class PermissionAdminChecker(PermissionUserLevelChecker):
    ref_v = True # True -> 관리자