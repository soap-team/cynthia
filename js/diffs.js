// Initialize Firebase
var firebaseConfig = {
    apiKey: "AIzaSyBTRD3nJ4ChBZQ4dS9mXwoq43Kc0mkj3rM",
    authDomain: "soap-cynthia.firebaseapp.com",
    databaseURL: "https://soap-cynthia.firebaseio.com",
    projectId: "soap-cynthia",
    storageBucket: "soap-cynthia.appspot.com",
    messagingSenderId: "950952379277",
    appId: "1:950952379277:web:10b086eebee1cd61b3f3c4"
};
firebase.initializeApp(firebaseConfig);
var db = firebase.database();

var dataset = 'en';
var diffLink = '';

/**
 * Login via Firebase to enable write access
 * @param  password the password for the Firebase user
 */
function login(password) {
    $('#diff').empty().append("Loading diff...");
    firebase.auth().signInWithEmailAndPassword('noreply@fandom.com', password).then(function() {
        console.log('logged in');
    }).catch(function(error) {
        $('body').append('Error: ' + error.message);
    });
}

// Log out of Firebase
function logout() {
    firebase.auth().signOut().then(function(d) {
        console.log('logged out');
    }).catch(function(error) {
        $('body').append('Error: ' + error.message);
    });
}

/**
 * Checks if the user is logged in
 * @return  true if logged in, false otherwise
 */
function isLoggedIn() {
    return firebase.auth().currentUser != null ? true : false;
}

// Displays the diff
function showDiff(wiki, revid) {
    $('#diff').empty().append("Loading diff...");
    $.get('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').then(function(d) {
        if (d.query.pages != null) {
            $('#diff').empty().append('<h3>' + d.query.pages[Object.keys(d.query.pages)[0]].title + '</h3>');
            $('#diff').append('comment: ' + d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].comment + '<br>');
            $('#diff').append('<a href="' + diffLink + '">' + diffLink + '</a>');
            $('#diff').append('<table id="table"></table>');
            $('#diff-display').show();
            $('#dataset-select').hide();
            console.log('showing ' + wiki + revid);
            $('#table').empty().append(d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].diff['*']);
            $('#categories').show();
        } else {
            $('body').html('<div>Diff does not exist.</div>');
        }
   });
}

// Categories the diff
function categoriseDiff(wiki, revid) {
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

    dbRef = db.ref('uncategorised/' + dataset + '/');
    db.ref('uncategorised/' + dataset + '/').once('value').then(function(snapshot) {
        console.log('removed ' + wiki + revid);
        console.log('removed key: ' + Object.keys(snapshot.val())[0]);
        dbRef.child(Object.keys(snapshot.val())[0]).remove();

        db.ref('uncategorised/' + dataset + '/').once('value').then(function(s) {
            s.forEach(function(e) {
                diffLink = e.val();
                wiki = diffLink.split('wiki')[0];
                revid = diffLink.split('diff=').pop();
                showDiff(wiki, revid);
                return true;
            });         
        });
    });
}

// Gets the names of each uncategorised dataset in the firebase database and 
// adds buttons to the interface for each dataset
function getDatasetList() {
    db.ref('uncategorised/').once('value').then(function(snapshot) {
        $('#dataset').empty();
        Object.keys(snapshot.val()).forEach(function(e) {
            $('#dataset').append('<button class="dataset-buttons" data-id="' + e + '">' + e + '</button><br>');
        });
    });
}

// Initialises the system
function init() {
    firebase.auth().onAuthStateChanged(function(user) {
        console.log(isLoggedIn());
        if (user) {
            $('#login-form').hide();
            $('#diff-display').hide();
            getDatasetList();
            $('#dataset-select').show();
        } else {
            $('#login-form').show();
            $('#dataset-select').hide();
            $('#diff-display').hide();
        }
    });
    $('#login-button').on('click', function() {
        login($('#password').val());
        $('#password').val("");
        console.log($('#dataset option:selected').val());
        dataset = $('#dataset option:selected').val();
    });
    $('#next').on('click', function() {
        var wiki = diffLink.split('wiki')[0];
        var revid = diffLink.split('diff=').pop();
        categoriseDiff(wiki, revid);
        
        $("#damaging").prop("checked", false);
        $("#spam").prop("checked", false);
        $("#goodfaith").prop("checked", false);
        $("#good").prop("checked", false);
    });
    $('#dataset').on('click', '.dataset-buttons', function() {
        dataset = $(this).text();
        console.log(dataset);
        db.ref('uncategorised/' + dataset + '/').once('value').then(function(snapshot) {
            snapshot.forEach(function(e) {
                diffLink = e.val();
                var wiki = diffLink.split('wiki')[0];
                var revid = diffLink.split('diff=').pop();
                showDiff(wiki, revid);
                return true;
            });
        });
    });
    $('#dataset-select-button').on('click', function() {
        $('#diff-display').hide();
        getDatasetList();
        $('#dataset-select').show();
    });
    $('#login-form form').submit(function(e) {
        e.preventDefault();
    });
    $('#categories form').submit(function(e) {
        e.preventDefault();
    });
}

// Runs the initialisation
$(function() {
    init();
});
/*
showDiff('https://ff14-light.fandom.com/de/', '12925');
https://leagueoflegends.fandom.com/wiki/?diff=2984657
showDiff('https://leagueoflegends.fandom.com/', '2984657');
$.get('https://cors-anywhere.herokuapp.com/https://dontstarve.fandom.com/api.php?action=query&prop=revisions&revids=461184&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').then(function(d){console.log(d)});
*/