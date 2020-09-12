from revscoring.features import revision_oriented

page = [
    revision_oriented.revision.page.namespace.id_in_set(
        {0, 2, 10, 14}, name="revision.page.is_usually_vandalized"),
    revision_oriented.revision.page.namespace.id_in_set(
        {0}, name="revision.page.is_mainspace")
]