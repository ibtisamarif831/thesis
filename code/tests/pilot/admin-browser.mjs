// Test-only preview key is read locally and never printed in browser/tool logs.
import {readFileSync,writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
const key=JSON.parse(readFileSync('tmp/pilot-preview-secrets.json')).STUDY_ADMIN_KEY;
const title='PREVIEW UI TEST — administrator workflow '+crypto.randomUUID().slice(0,8);
const code=`async (page) => {
 await page.getByRole('button',{name:'Submissions',exact:true}).click();
 await page.locator('#resultsAccessKey').fill(${JSON.stringify(key)});
 await page.getByRole('button',{name:'Refresh results',exact:true}).click();
 await page.getByRole('button',{name:'Create pilot',exact:true}).waitFor();
 await page.getByRole('button',{name:'Create pilot',exact:true}).click();
 await page.getByRole('heading',{name:'Create frozen pilot',exact:true}).waitFor();
 if(await page.locator('.pilot-icon-preview img').count()!==20) throw new Error('Preview is not 20 icons');
 await page.locator('#pilotTitle').fill(${JSON.stringify(title)});
 if(await page.locator('#pilotSizes').count()) throw new Error('Legacy size editor remains');
 if(!(await page.locator('#pilotDialogBody').textContent()).includes('100 randomized recorded trials')) throw new Error('Controlled protocol missing');
 await page.locator('#pilotCreateSubmit').click();
 await page.locator('#pilotDialog').waitFor({state:'hidden'});
 const row=page.locator('.pilot-admin-row').filter({hasText:${JSON.stringify(title)}});
 await row.getByRole('button',{name:'View configuration'}).click();
 await page.locator('#pilotDialogBody pre').waitFor();
 if(!(await page.locator('#pilotDialogBody pre').textContent()).includes('icon-recognition-controlled-v2')) throw new Error('Missing frozen protocol');
 await page.locator('#closePilotDialog').click();
 await row.getByRole('button',{name:'View results'}).click();
 await page.getByRole('heading',{name:'assigned icon size (CSS pixels)',exact:true}).waitFor();
 await page.locator('#closePilotDialog').click();
 for(const label of ['Trial CSV','Full JSON']) {const download=page.waitForEvent('download'); await row.getByRole('button',{name:label,exact:true}).click(); await download;}
 await row.getByRole('button',{name:'Close pilot',exact:true}).click();
 await row.getByText('Closed',{exact:true}).waitFor();
 if(await row.getByRole('button',{name:'Close pilot',exact:true}).count()) throw new Error('Closed pilot can be closed again');
 await page.locator('#resultsAccessKey').fill('');
 await page.locator('#pilotAccessKey').fill('');
}`;
try {
 const output=execFileSync('/Users/macbook/.codex/skills/playwright/scripts/playwright_cli.sh',['-s=pilot-admin','run-code',code],{encoding:'utf8',maxBuffer:4e6});
 writeFileSync('tmp/pilot-admin-browser.log',output,{mode:0o600});
 if(output.includes('### Error')) throw new Error('Browser reported failure');
 console.log('PASS: preview admin UI, 20-icon creation dialog, immutable configuration inspection, summaries, CSV/JSON downloads, and closure.');
} catch(error) {writeFileSync('tmp/pilot-admin-browser-error.log',String(error.stdout || error.message),{mode:0o600});console.error('Admin browser test failed; details saved in private tmp log.');process.exitCode=1;}
