/**
 * This script moves new, highly-scored diffs to the review queue in the labelling interface.
 * It does this by generating worksets and placing them into Firebase.
 * @author Noreplyz
 */
const fs = require('fs');
const readline = require('readline');
const admin = require("firebase-admin");

/**
 * Parses score files into an array of diffs that meet a threhold
 * @param  {String} file score.log
 * @return {String}      array of diff links
 */
async function parseScoreFile(file, threshold) {
    let diffs = [], scores = [];
    const fileStream = fs.createReadStream(file);
    const rl = readline.createInterface({
        input: fileStream,
        crlfDelay: Infinity
    });

    for await (const line of rl) {
        // console.log(line);
        // Ignore errors
        if (line.includes('] ERROR:')) continue;
        let [,,wiki, diffid, model, score] = line.split(',');
        score = parseFloat(score);
        // console.log(score);
        // Ignore non-numbers, and scores under the threshold
        if (isNaN(score) || score < threshold) continue;

        diffs.push(`https://${wiki}/wiki/?diff=${diffid}`);
        scores.push(score);
    }

    return [diffs, scores];
}

/**
 * Connect to the Firebase instance
 * @return Firebase database
 */
function connect() {
    let serviceAccount = require("./soap-cynthia-firebase-key-secret-wow.json");

    admin.initializeApp({
        credential: admin.credential.cert(serviceAccount),
        databaseURL: "https://soap-cynthia.firebaseio.com"
    });

    // The app only has access as defined in the Security Rules
    let db = admin.database();
    return db;
}

async function getWorksetsToClean(db, datasetName, days) {
    let daysinms = days * 24 * 60 * 60 * 1000;
    let datasetRef = db.ref(`categorised/${datasetName}/`);
    await datasetRef.remove();

    let worksets = [];
    datasetRef = db.ref(`datasets/${datasetName}/`);
    await datasetRef.once('value', function(snap) {
        Object.keys(snap.val()).forEach((ws) => {
            let wsDate = new Date(ws.slice(3, 23));
            
            // If the workset is old enough, delete from db
            if (new Date() - wsDate > daysinms) {
                worksets.push(ws);
            }
        });
    });

    return worksets;
}

async function run() {
    // Get config
    let configRaw = fs.readFileSync('./config.json');
    let config = JSON.parse(configRaw);

    if (!config.enabled) {
        return;
    }

    fs.renameSync(config.scores_file, 'scores-temp.log');

    // Get diffs
    let [diffs, scores] = await parseScoreFile('scores-temp.log', config.threshold);
    // Split diffs into worksets
    let worksets = [], worksetScores = [];
    while (diffs.length) {
        worksets.push(diffs.splice(0, 20));
        worksetScores.push(scores.splice(0, 20));
    }

    let db = connect(),
        datasetName = config.dataset_name;

    // Store actual diffs into /uncategorised/
    let datasetRef = db.ref(`uncategorised/${datasetName}/`);
    let datasetStatuses = {}; // used to fill in /datasets/ in Firebase
    let datasetScores = {}; // used to fill in /scores/ in Firebase

    let datetime = new Date().toISOString().slice(0,19) + 'Z';
    for (let wsid in worksets) {
        let worksetname = `ws-${datetime}-${wsid}`;
        let data = {};
        data[worksetname] = worksets[wsid];
        await datasetRef.update(data);
        datasetStatuses[worksetname] = 0;
        datasetScores[worksetname] = worksetScores[wsid];
        // console.log(`uploaded workset ${worksetname}`);
    }

    // Update /datasets/
    datasetRef = db.ref(`datasets/${datasetName}/`);
    await datasetRef.update(datasetStatuses);

    // Update /scores/
    datasetRef = db.ref(`scores/${datasetName}/`);
    await datasetRef.update(datasetScores);

    fs.unlinkSync('scores-temp.log');

    // Clean up Firebase if requested
    if (config.perform_cleanup) {
        let worksetsToClean = await getWorksetsToClean(db, datasetName, config.days_before_cleanup);

        for (let ws of worksetsToClean) {
            let wsCleanRef = db.ref(`scores/${datasetName}/${ws}/`);
            await wsCleanRef.remove();
            wsCleanRef = db.ref(`uncategorised/${datasetName}/${ws}/`);
            await wsCleanRef.remove();
            wsCleanRef = db.ref(`datasets/${datasetName}/${ws}/`);
            await wsCleanRef.remove();
        }
    }
    admin.app().delete();
}

run();