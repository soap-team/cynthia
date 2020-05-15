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

var dataset = '';
var diffList = [];

/**
 * Login via Firebase to enable write access
 * @param  type the type of login as a string
 * @param  password the password for the Firebase user
 */
function login(password) {
    firebase.auth().signInWithEmailAndPassword('noreply@fandom.com', password).then(function() {
        console.log('logged in');
        $('#login-form').hide();
        db.ref('uncategorised/' + dataset + '/').once('value').then(function(snapshot) {
            snapshot.val().forEach(function(e) {
                diffList.push(e);
            })
            var wiki = diffList[0].split('wiki')[0];
            var revid = diffList[0].split('diff=').pop();
            console.log('l wiki and revid ' + wiki + revid);
            showDiff(wiki, revid);
        });
    }).catch(function(error) {
        $('body').append('Error: ' + error.message);
    });
}

// Log out of Firebase
function logout() {
    firebase.auth().signOut().then(function(d) {
        console.log("logged out");
    }).catch(function(error) {
        $('body').append('Error: ' + error.message);
    });
}

function showDiff(wiki, revid) {
   $.get('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').then(function(d) {
        if (d.query.pages != null) {
            $('#table').empty().append(d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].diff['*']);
            $('#categories').show();
        } else {
            $('body').html('<div>Diff does not exist.</div>');
        }
   });
}

function categoriseDiff(wiki, revid) {
    console.log('c wiki and revid ' + wiki + revid);
    var newDiffKey = db.ref('categorised/' + dataset + '/').push().key;
    var dbRef = db.ref('categorised/' + dataset + '/' + newDiffKey + '/');
    dbRef.set({
        diff: wiki + 'wiki/?diff=' + revid,
        categories: {
            damaging: 0,
            spam: 0,
            goodfaith: 0,
            good: 0
        }
    })
    var checked = $('input[name=options]:checked');
    checked.each(function() {
        dbRef.child('categories/' + this.id).set(1);
    });
}

function init() {
    $('#categories').hide();
    $('#login').on('click', function() {
        login($('#password').val());
        $('#password').val("");
        console.log($('#dataset option:selected').val());
        dataset = $('#dataset option:selected').val();
    });
    // need to check if option selected
    $('#submit').on('click', function() {
        var wiki = diffList[0].split('wiki')[0];
        var revid = diffList[0].split('diff=').pop();
        categoriseDiff(wiki, revid);
        console.log("categorised");
        var dbRef = db.ref('uncategorised/' + dataset + '/');
        db.ref('uncategorised/' + dataset + '/').once('value').then(function(snapshot) {
            console.log('removed key: ' + Object.keys(snapshot.val())[0]);
            dbRef.child(Object.keys(snapshot.val())[0]).remove();
        });
        console.log(diffList[0]);
        diffList.shift();
        console.log(diffList[0]);
        
        $("#damaging").prop("checked", false);
        $("#spam").prop("checked", false);
        $("#goodfaith").prop("checked", false);
        $("#good").prop("checked", false);
        showDiff(wiki, revid);
    });

}

$(function() {
    init();
});
//showDiff('https://ff14-light.fandom.com/de/', '12925');
//'https://leagueoflegends.fandom.com/wiki/?diff=2984657'
//showDiff('https://leagueoflegends.fandom.com', '2984657');