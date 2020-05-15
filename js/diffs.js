// Initialize Firebase
var config = {
    apiKey: 'AIzaSyBTRD3nJ4ChBZQ4dS9mXwoq43Kc0mkj3rM',
    authDomain: 'soap-cynthia.firebaseapp.com',
    databaseURL: 'https://soap-cynthia.firebaseio.com',
    projectId: 'soap-cynthia',
    storageBucket: 'soap-cynthia.appspot.com',
    messagingSenderId: '950952379277'
};
firebase.initializeApp(config);
var db = firebase.database();

/**
 * Login via Firebase to enable write access
 * @param  type the type of login as a string
 * @param  password the password for the Firebase user
 */
function login(password) {
    firebase.auth().signInWithEmailAndPassword('noreply@fandom.com', password).then(function() {
        console.log('logged in');
        $('#login-form').hide();
        showDiff('https://leagueoflegends.fandom.com/', '2984657');
    }).catch(function(error) {
        $('body').append('Error: ' + error.message);
    });
}

// Log out of Firebase
function logout() {
    firebase.auth().signOut().then(function(d) {
        console.log("logged out");
    }).catch(function(error) {
        $('body').append(error.code + ' Error: ' + error.message);
    });
}

function showDiff(wiki, revid) {
   $.get('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').then(function(d) {
        if (d.query.pages != null) {
            $('body').append('<div id="diff"></div>');
            $('#diff').append('<table id="table"></table>');
            $('#table').append(d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].diff['*']);

            $('body').append('<div id="categories"></div>');
            $('#categories').append('<input type="checkbox" id="damaging" name="options">');
            $('#categories').append('<label for="damaging">Damaging</label><br>');

            $('#categories').append('<input type="checkbox" id="spam" name="options">');
            $('#categories').append('<label for="spam">Spam</label><br>');

            $('#categories').append('<input type="checkbox" id="goodfaith" name="options">');
            $('#categories').append('<label for="goodfaith">Goodfaith</label><br>');

            $('#categories').append('<input type="checkbox" id="good" name="options">');
            $('#categories').append('<label for="good">Good</label><br>');

            $('#categories').append('<button type="submit" id="submit" onClick="categoriseDiff()">Submit</button>');

        } else {
            $('body').html('<div id="diff">Diff does not exist.</div>');
        }
   });
}

function categoriseDiff() {
    var checked = $('input[name=options]:checked');
    checked.each(function() {
        console.log(this.id);
    });
}

function init() {
    /*
    firebase.auth().onAuthStateChanged(function(user) {
        if (user) {
            showDiff('https://leagueoflegends.fandom.com/', '2984657');
        }
    });*/
    $('#login').on('click', function() {
        login($('#password').val());
        $('#password').val("");
    });
}

$(function() {
    init();
});
//showDiff('https://ff14-light.fandom.com/de/', '12925');
//'https://leagueoflegends.fandom.com/wiki/?diff=2984657'