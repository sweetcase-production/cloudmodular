
def tag_validator(tag: str):
	if not isinstance(tag, str) or not (0 < len(tag) <= 32):
		return False
	no_uses = {'/', '\\', ':', '*', '"', "'", '<', '>', '|', ','}
	return (not tag) or (not any([c in tag for c in no_uses]))
