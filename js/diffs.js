function showDiff(wiki, revid) {
   console.log('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json');

   $.get('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').done(function(d) {
        if (d.query.pages != null) {
            console.log(d);
            $('body').html('<div id="diff"></div>');
            $('#diff').append('<table></table>');
            $('#diff').append(d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].diff['*']);

            $('body').append('<div id="categories"></div>');
            $('#categories').append('<input type="checkbox" id="damaging" name="options">');
            $('#categories').append('<label for="damaging">Damaging</label><br>');

            $('#categories').append('<input type="checkbox" id="spam" name="options">');
            $('#categories').append('<label for="spam">Spam</label><br>');

            $('#categories').append('<input type="checkbox" id="goodfaith" name="options">');
            $('#categories').append('<label for="goodfaith">Goodfaith</label><br>');

            $('#categories').append('<input type="checkbox" id="good" name="options">');
            $('#categories').append('<label for="good">Good</label><br>');

            $('#categories').append('<button id="submit" onClick="categoriseDiff()">Submit</button>');

        } else {
            $('body').html('<div id="diff">No diff to show!</div>');
        }
   });
}

function categoriseDiff() {
    var checked = $('input[name=options]:checked');
    checked.each(function() {
        console.log(this.id);
    });
}

showDiff('https://leagueoflegends.fandom.com/', '2984657');
//showDiff('https://ff14-light.fandom.com/de/', '12925');
