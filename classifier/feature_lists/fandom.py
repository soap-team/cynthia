from revscoring.features import wikitext as wikitext_features
from revscoring.features import revision_oriented
from revscoring.languages.features import RegexMatches
from revscoring.features.modifiers import sub
from revscoring.languages import english

from . import mediawiki, wikipedia, wikitext

local_wiki = [
    revision_oriented.revision.comment_matches(
        r"^delet",
        name="fandom.revision.comment.delete_request"
    ),
    sub(
        wikitext_features.revision.template_names_matching(r"^delet"),
        wikitext_features.revision.parent.template_names_matching(r"^delet"),
        name="fandom.revision.diff.delete_added"
    ),
    sub(
        wikitext_features.revision.wikilink_titles_matching(r"^category:(delet|candidat)"),
        wikitext_features.revision.parent.wikilink_titles_matching(r"^category:(delet|candidat)"),
        name="fandom.revision.diff.delete_category_added"
    ),
    revision_oriented.revision.comment_matches(
        r"^redirected page to",
        name="fandom.revision.comment.likely_redirect"
    )
]

# Redirect page
redirect_regex = r"redirect"
redirects = RegexMatches("fandom.likely_redirect", [redirect_regex])

badwords = [
    english.badwords.revision.diff.match_delta_sum,
    english.badwords.revision.diff.match_delta_increase,
    english.badwords.revision.diff.match_delta_decrease,
    english.badwords.revision.diff.match_prop_delta_sum,
    english.badwords.revision.diff.match_prop_delta_increase,
    english.badwords.revision.diff.match_prop_delta_decrease
]

redirects_m = [
    redirects.revision.diff.match_delta_sum,
    redirects.revision.diff.match_delta_increase,
    redirects.revision.diff.match_delta_decrease,
    redirects.revision.diff.match_prop_delta_sum,
    redirects.revision.diff.match_prop_delta_increase,
    redirects.revision.diff.match_prop_delta_decrease
]

informals = [
    english.informals.revision.diff.match_delta_sum,
    english.informals.revision.diff.match_delta_increase,
    english.informals.revision.diff.match_delta_decrease,
    english.informals.revision.diff.match_prop_delta_sum,
    english.informals.revision.diff.match_prop_delta_increase,
    english.informals.revision.diff.match_prop_delta_decrease
]

dict_words = [
    english.dictionary.revision.diff.dict_word_delta_sum,
    english.dictionary.revision.diff.dict_word_delta_increase,
    english.dictionary.revision.diff.dict_word_delta_decrease,
    english.dictionary.revision.diff.dict_word_prop_delta_sum,
    english.dictionary.revision.diff.dict_word_prop_delta_increase,
    english.dictionary.revision.diff.dict_word_prop_delta_decrease,
    english.dictionary.revision.diff.non_dict_word_delta_sum,
    english.dictionary.revision.diff.non_dict_word_delta_increase,
    english.dictionary.revision.diff.non_dict_word_delta_decrease,
    english.dictionary.revision.diff.non_dict_word_prop_delta_sum,
    english.dictionary.revision.diff.non_dict_word_prop_delta_increase,
    english.dictionary.revision.diff.non_dict_word_prop_delta_decrease
]

damaging = wikipedia.page + \
    wikitext.parent + wikitext.diff + mediawiki.user_rights + \
    mediawiki.protected_user + mediawiki.comment + \
    badwords + informals + dict_words + local_wiki + \
    redirects_m
"Damaging Features"

reverted = damaging
goodfaith = damaging