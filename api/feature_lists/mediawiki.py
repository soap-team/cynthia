from revscoring.features import revision_oriented, temporal
from revscoring.features.modifiers import log

comment = [
    revision_oriented.revision.comment_matches(
        r"^/\* [^\n]+ \*/",
        name="revision.comment.suggests_section_edit"
    ),
    revision_oriented.revision.comment_matches(
        r".*\[\[[^\]]+\]\].*",
        name="revision.comment.has_link"
    )
]

user_rights = [
    revision_oriented.revision.user.in_group(
        {'bot'}, name="revision.user.is_bot"),
    revision_oriented.revision.user.in_group(
        {'checkuser', 'staff', 'vstf', 'soap', 'helper', 
        'wiki-manager', 'content-team-member', 'bot-global'},
        name="revision.user.has_global_rights"),
    revision_oriented.revision.user.in_group(
        {'sysop', 'bureaucrat'}, name="revision.user.has_admin_rights"),
    revision_oriented.revision.user.in_group(
        {'rollback', 'discussions-threadmoderator', 
        'content-moderator', 'chatmoderator'}, 
        name="revision.user.has_mod_rights"),
]

protected_user = [
    revision_oriented.revision.user.is_anon,
    log(temporal.revision.user.seconds_since_registration + 1)
]