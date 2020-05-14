function showDiff(wiki, revid) {
   console.log('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json');

   $.get('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').done(function(d) {
        console.log(d);
        $('body').html('<div id="hello"></div>');
        $('#hello').append('<table></table>');
        $('#hello').append(d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].diff['*']);
   });
}

showDiff('https://leagueoflegends.fandom.com/', '2984657');