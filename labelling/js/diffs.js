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

var dataset = '';
var diffLink = '';
var workset = '';

var keypressEnabled = false;

// Constants
var inUse = 1;
var notInUse = 0;

$('#next').prop('disabled', true);

function escapeHTML(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }

/**
 * Login via Firebase to enable write access
 * @param  password the password for the Firebase user
 */
function login(password) {
    $('#diff-container').empty().append("Loading diff...");
    firebase.auth().signInWithEmailAndPassword('noreply@fandom.com', password).then(function() {
        console.log('logged in');
        $('#login-message').empty().append('Logging in...');
        $('#login-message').show();
    }).catch(function(error) {
        $('#login-message').empty().append('Error: ' + error.message);
        $('#login-message').show();
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

// Gets the names of each uncategorised dataset in the firebase database and 
// adds buttons to the interface for each dataset
function getDatasetList() {
    db.ref('datasets/').once('value').then(function(snapshot) {
        $('#dataset').empty();
        if (snapshot.exists()) {
            snapshot.forEach(function(e) {
                $('#dataset').append('<button class="dataset-buttons tile" data-id="' + e.key + '">' + e.key + 
                    ' <span style="font-weight:normal; float:right">(approx ' + Object.keys(e.val()).length * 20 + ' left)</span></button>');
            });
        } else {
            $('#dataset-message').hide();
            $('#dataset').append('Datasets all complete.');
        }
    });
}

// Assigns the first available workset in the dataset to the user
function assignWorkset() {
    dbRef = db.ref('datasets/' + dataset + '/');
    dbRef.once('value').then(function(snapshot) {
        if (snapshot.exists()) {
            var found = false;
            snapshot.forEach(function(e) {
                if (e.val() === 0) {
                    $('#dataset-message').hide();
                    found = true;
                    workset = e.key;
                    dbRef.child(workset).set(inUse);
                    dbRef.child(workset).onDisconnect().set(notInUse);
                    console.log(dataset + '/' + workset + ' now in use');
                    getNextDiff();
                    return true;
                } else {
                    console.log(dataset + '/' + e.key + ' in use');
                }
            });
            if (!found) {
                $('#dataset-message').empty().append('No available worksets for ' + dataset + '. Please select another dataset.');
                if (workset !== '') {
                    $('#diff-display').hide();
                    getDatasetList();
                    $('#dataset-select').show();
                }
                    $('#dataset-message').show();
            }
        } else {
            workset = '';
            dataset = '';
            $('#dataset-message').empty().append('The dataset you selected has been completed. Please select another.');
            $('#dataset-message').show();
            $('#diff-display').hide();
            getDatasetList();
            $('#dataset-select').show();
        }
    });
}

// Gets the next diff in the workset and shows it
function getNextDiff() {
    console.log('getting next diff');
    db.ref('uncategorised/' + dataset + '/' + workset + '/').once('value').then(function(snapshot) {
        if (snapshot.exists()) {
            snapshot.forEach(function(e) {
                diffLink = e.val();
                var wiki = diffLink.split('wiki/')[0];
                var revid = diffLink.split('diff=').pop();
                showDiff(wiki, revid);
                return true;
            });    
        } else {
            console.log('workset finished');
            dbRef = db.ref('datasets/' + dataset + '/' + workset + '/');
            dbRef.onDisconnect().cancel();
            if (dataset !== '' and workset !== '') {
                dbRef.remove();
            } else {
                console.log("Error removing workset");
            }
            assignWorkset();
        }
    });
}

// Displays the diff
function showDiff(wiki, revid) {
    keypressEnabled = true;
    $('#diff-container').empty().append("Loading diff...");
    $.get('https://calm-oasis-68089.herokuapp.com/' + wiki + 'api.php?action=query&prop=revisions&revids=' + revid +
            '&rvprop=ids|timestamp|flags|comment|user|content&rvdiffto=prev&format=json').then(function(d) {
        if (d.query.pages) {
            $('#diff-container').empty().append('<h3>' + d.query.pages[Object.keys(d.query.pages)[0]].title + '</h3>');
            $('#diff-container').append('comment: ' + d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].comment + '<br/>');
            $('#diff-container').append('<a href="' + diffLink + '" target="_blank">' + diffLink + '</a>');
            $('#diff-container').append('<table id="diff" class="diff"><tbody></tbody></table>');
            $('#diff').prepend('<colgroup><col class="diff-marker">' +
                '<col class="diff-content">' +
                '<col class="diff-marker">' +
                '<col class="diff-content">' +
                '</colgroup>');
            $('#diff-display').show();
            $('#dataset-select').hide();
            if (!d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].diff.from) {
                var content = d.query.pages[Object.keys(d.query.pages)[0]].revisions[0]['*'];
                content = escapeHTML(content);
                content = content.split('\n');
                $('#diff tbody').empty();
                $('#diff tbody').append('<tr><td/><td/><td colspan="2" class="diff-lineno">Line 1:</td></tr>');
                content.forEach(function(e) {
                    $('#diff tbody').append('<tr><td/><td/> <td class="diff-marker">+</td><td class="diff-addedline"><div>' + e + '</div></td></tr>');
                });
                console.log('diff is a new page');
            } else {
                $('#diff tbody').empty().append(d.query.pages[Object.keys(d.query.pages)[0]].revisions[0].diff['*']);
            }
            console.log('showing ' + wiki + 'wiki/?diff=' + revid);
            $('#categories').show();
            $('#next').prop('disabled', false);
        } else {
            console.log('skipping deleted diff, ' + wiki + 'wiki/?diff=' + revid + ' removed from db');
            deleteFirstDiff();
        }
   }).catch(function() {
        console.log('skipping deleted wiki/broken link, ' + wiki + 'wiki/?diff=' + revid + ' removed from db');
        deleteFirstDiff();
   });
}

// Categories the diff
function categoriseDiff(wiki, revid) {
    if (dataset !== '') {
        var newDiffKey = db.ref('categorised/' + dataset + '/').push().key;
        var dbRef = db.ref('categorised/' + dataset + '/' + newDiffKey + '/');
        dbRef.set({
            diff: wiki + 'wiki/?diff=' + revid,
            labels: {
                damaging: 0,
                spam: 0,
                goodfaith: 0
            }
        })
        var checked = $('input[name=options]:checked');
        checked.each(function() {
            dbRef.child('labels/' + this.id).set(1);
        });
    } else {
        console.log('Error categorising diff');
    }

    deleteFirstDiff();
}

// Deletes the first key in the workset and gets the next one
function deleteFirstDiff() {
    dbRef = db.ref('uncategorised/' + dataset + '/' + workset + '/');
    dbRef.once('value').then(function(snapshot) {
        console.log('removed key: ' + Object.keys(snapshot.val())[0]);
        if (dataset !== '' and workset !== '') {
            dbRef.child(Object.keys(snapshot.val())[0]).remove();
        } else {
            console.log("Error deleting diff");
        }
        getNextDiff();
    });
}

// Initialises the app
function init() {
    firebase.auth().onAuthStateChanged(function(user) {
        console.log(isLoggedIn());
        if (user) {
            $('#login-form').hide();
            $('#diff-display').hide();
            $('#login-message').hide();
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
    });
    $('#next').on('click', function() {
        if ($(this).prop('disabled') || $(this).is(':disabled') || $(this).attr('disabled')) {
            return;
        } else {
            $('#next').prop('disabled', true);
        }
        var wiki = diffLink.split('wiki/')[0];
        var revid = diffLink.split('diff=').pop();
        categoriseDiff(wiki, revid);
        
        $('#damaging').prop('checked', false);
        $('#spam').prop('checked', false);
        $('#goodfaith').prop('checked', false);
    });
    $('#dataset').on('click', '.dataset-buttons', function() {
        dataset = $(this).data('id');
        console.log(dataset);
        assignWorkset();
    });
    $('#dataset-select-button').on('click', function() {
        keypressEnabled = false;
        $('#diff-display').hide();
        $('#next').prop('disabled', true);
        db.ref('datasets/' + dataset + '/' + workset + '/').set(notInUse);
        dataset = '';
        workset = '';
        getDatasetList();
        $('#dataset-select').show();
    });
    $('#login-form form').submit(function(e) {
        e.preventDefault();
    });
    $('#categories form').submit(function(e) {
        e.preventDefault();
    });

    // Keyboard shortcuts
    $(document).keypress(function (e) {
        if (keypressEnabled) {
            if (e.charCode === 100) { // d
                $('#damaging').prop('checked', !$('#damaging').prop('checked'));
            }
            else if (e.charCode === 115) { // s
                $('#spam').prop('checked', !$('#spam').prop('checked'));
            }
            else if (e.charCode === 103) { // g
                $('#goodfaith').prop('checked', !$('#goodfaith').prop('checked'));
            }
            else if (e.charCode === 110) {
                $('#next').click();
            }
        }
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
https://skyblock.fandom.com/wiki/Skyblock_Roblox_Wiki?diff=527
"2020-05-20T12:48:03.710Z"
*/