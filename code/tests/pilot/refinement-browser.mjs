// Run only against the integration suite's isolated local server.
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
const base=process.argv[2];
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(base))throw Error('Local integration server required');
const cli='/Users/macbook/.codex/skills/playwright/scripts/playwright_cli.sh';
const run=(...args)=>{const out=execFileSync(cli,['--session=pilot-refinement',...args],{encoding:'utf8',maxBuffer:4e6});if(out.includes('### Error'))throw Error(out);return out;};
try {
 run('open',base+'/study-selection.html');
 run('snapshot');
 const admin=`async page => {
 await page.getByRole('button',{name:'Submissions',exact:true}).click();
 await page.locator('#resultsAccessKey').fill('local-admin');
 await page.getByRole('button',{name:'Refresh results',exact:true}).click();
 await page.getByRole('button',{name:'Create pilot',exact:true}).click();
 await page.locator('#pilotTitle').fill('LOCAL BROWSER refinement');
 if(!(await page.locator('#pilotDialogBody').textContent()).includes('ranks 12–16'))throw Error('Band missing in creation dialog');
 await page.locator('#pilotCreateSubmit').click();await page.locator('#pilotDialog').waitFor({state:'hidden'});
 const row=page.locator('.pilot-admin-row').filter({hasText:'LOCAL BROWSER refinement'});
 await row.getByRole('button',{name:'View configuration'}).click();await page.locator('#pilotDialogBody pre').waitFor();
 const cfg=JSON.parse(await page.locator('#pilotDialogBody pre').textContent());
 if(!cfg.selection_seed||!cfg.image_hashes||cfg.schedule_rule_version!=='balanced-target-positions-v1')throw Error('Missing audit metadata');
 await page.locator('#closePilotDialog').click();
 await row.getByRole('button',{name:'View results'}).click();
 await page.locator('#pilotDialogBody').getByText(/Standardized rendering collision diagnostics:/).waitFor();
 if(!(await page.locator('#pilotDialogBody').textContent()).includes('collision diagnostics: checked'))throw Error('Missing collision status');
 await page.locator('#closePilotDialog').click();
 for(const [label,format] of [['Trial CSV','csv'],['Full JSON','full']]) {
 const waiting=page.waitForEvent('download');await row.getByRole('button',{name:label,exact:true}).click();const d=await waiting;
 const stream=await d.createReadStream();let content='';for await(const chunk of stream)content+=chunk.toString();
 if(format==='csv'?!content.includes('collision_check_status'):!JSON.parse(content).pilot.config.image_hashes)throw Error('Missing exported evidence');
 }
 const old=page.locator('.pilot-admin-row').filter({hasText:'legacy fixture'});
 await old.getByRole('button',{name:'View results'}).click();
 await page.locator('#pilotDialogBody').getByText(/Standardized rendering collision diagnostics:/).waitFor();
 if(!(await page.locator('#pilotDialogBody').textContent()).includes('not checked'))throw Error('Legacy falsely checked');
 await page.locator('#closePilotDialog').click();
 }`;
 run('run-code',admin);
 const pilots=await (await fetch(base+'/api/pilots',{headers:{Authorization:'Bearer local-admin'}})).json();
 const pilot=pilots.pilots.find(p=>p.title==='LOCAL BROWSER refinement');
 run('goto',base+'/pilot.html?pilot='+pilot.invitation);run('snapshot');
 run('run-code',readFileSync('code/tests/pilot/controlled-browser.js','utf8'));
 run('run-code',readFileSync('code/tests/pilot/keyboard-study-browser.js','utf8').replace('http://127.0.0.1:8799',base));
 console.log('PASS: isolated browser administration, rules/diagnostics, legacy not checked, CSV/JSON downloads, participant recovery and Windows/Mac keyboard flows.');
} finally {run('close');}
