## Review Script

This review script posts new, highly-scored edits into worksets on the [labelling interface](https://soap-team.github.io/cynthia/labelling).

## Use
* To turn on the review script, edit the config file such that `enabled: true`.
* The script should run twice a day, and this can be set up as a cron job or in pm2. It's done on pm2 in our instance.
	* Cynthia automatically publishes the scores into scores.log (from api/app.py)
	* The script renames the scores.log file to scores-temp.log. 
	* If the service is turned on, it copies those in temp into Cynthia, under new workset/s
	* Script deletes scores-temp.log
* To perform cleanup, the script also does the following in Firebase:
	* Deletes any entries in `categorised/v3-review`
	* Deletes any entries in worksets that are over a week old in `uncategorised/<workset>`
	* Worksets are stored with their date within their title, so this is how we track and delete old worksets.