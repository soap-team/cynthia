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

var dataset = 'en';
var diffLink = '';
//var diffList = [];

/**
 * Login via Firebase to enable write access
 * @param  password the password for the Firebase user
 */
function login(password) {
    $('#diff').empty().append("Loading diff...");
    firebase.auth().signInWithEmailAndPassword('noreply@fandom.com', password).then(function() {
        console.log('logged in');
        /*
        $('#login-form').hide();
        getDatasetList();
        $('#dataset').show();
        $('#diff').show();
        db.ref('uncategorised/' + dataset + '/').once('value').then(function(snapshot) {
            snapshot.forEach(function(e) {
                //console.log(e.val());
                diffLink = e.val();
                var wiki = diffLink.split('wiki')[0];
                var revid = diffLink.split('diff=').pop();
                showDiff(wiki, revid);
                return true;
                //diffList.push(e);
            });
            var wiki = diffList[0].split('wiki')[0];
            var revid = diffList[0].split('diff=').pop();
                     
        });
        */
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

function isLoggedIn() {
    return firebase.auth().currentUser != null ? true : false;
}

// Displays the diff
function showDiff(wiki, revid) {
    $('#diff').empty().append("Loading diff...");
    $.get('https://cors-anywhere.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid + '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').then(function(d) {
        if (d.query.pages != null) {
            $('#diff').empty().append('<table id="table"></table>');
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
                //console.log(e.val());
                diffLink = e.val();
                wiki = diffLink.split('wiki')[0];
                revid = diffLink.split('diff=').pop();
                showDiff(wiki, revid);
                return true;
                //diffList.push(e);
            });/*
            var wiki = diffList[0].split('wiki')[0];
            var revid = diffList[0].split('diff=').pop();
            */            
        });
    });
    //diffList.shift();
}

function getDatasetList() {
    db.ref('uncategorised/').once('value').then(function(snapshot) {
        $('#dataset').empty();
        Object.keys(snapshot.val()).forEach(function(e) {
            $('#dataset').append('<button class="dataset-buttons" data-id="' + e + '">' + e + '</button><br>');
            //$('#dataset').append('<option value="' + e + '">' + e + '</option>');
        });
    });
}

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
    // need to check if option selected
    $('#submit').on('click', function() {
        $("#damaging").prop("checked", false);
        $("#spam").prop("checked", false);
        $("#goodfaith").prop("checked", false);
        $("#good").prop("checked", false);

        var wiki = diffLink.split('wiki')[0];
        var revid = diffLink.split('diff=').pop();
        categoriseDiff(wiki, revid);
    });

    $('#dataset').on('click', '.dataset-buttons', function() {
        dataset = $(this).text();
        console.log(dataset);
        db.ref('uncategorised/' + dataset + '/').once('value').then(function(snapshot) {
            snapshot.forEach(function(e) {
                //console.log(e.val());
                diffLink = e.val();
                var wiki = diffLink.split('wiki')[0];
                var revid = diffLink.split('diff=').pop();
                showDiff(wiki, revid);
                return true;
                //diffList.push(e);
            });/*
            var wiki = diffList[0].split('wiki')[0];
            var revid = diffList[0].split('diff=').pop();
            */
        });
    });
    /*
    $('#dataset').change(function() {
        dataset = $('#dataset option:selected').val();
        console.log(dataset);
        $("#damaging").prop("checked", false);
        $("#spam").prop("checked", false);
        $("#goodfaith").prop("checked", false);
        $("#good").prop("checked", false);
        db.ref('uncategorised/' + dataset + '/').once('value').then(function(snapshot) {      
            snapshot.forEach(function(e) {
                //diffList.push(e);
                diffLink = e.val();
                var wiki = diffLink.split('wiki')[0];
                var revid = diffLink.split('diff=').pop();
                showDiff(wiki, revid);
                return true;
            });
            
            var wiki = diffList[0].split('wiki')[0];
            var revid = diffList[0].split('diff=').pop();
            
        });
    });
    */
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

$(function() {
    init();
});
//showDiff('https://ff14-light.fandom.com/de/', '12925');
//https://leagueoflegends.fandom.com/wiki/?diff=2984657
//showDiff('https://leagueoflegends.fandom.com/', '2984657');