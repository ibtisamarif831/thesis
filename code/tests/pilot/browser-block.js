// Playwright CLI run-code snippet; run after the participant has reached Ready.
async (page) => {
  await page.bringToFront();
  for(let i=0;i<10;i++) {
    if(await page.getByRole('button',{name:'Save and finish',exact:true}).count()) break;
    await page.getByRole('button',{name:'Ready',exact:true}).waitFor();
    const progress=await page.locator('#status').textContent();
    await page.getByRole('button',{name:'Ready',exact:true}).dblclick();
    await page.getByRole('button',{name:'Candidate 1',exact:true}).waitFor();
    if(await page.locator('.grid button').count()!==5) throw new Error('Incomplete grid');
    if(await page.locator('.grid [title],.grid figcaption').count()) throw new Error('Meaning-revealing grid');
    if(await page.evaluate(()=>document.documentElement.scrollHeight>innerHeight)) throw new Error('Grid requires scrolling');
    if(await page.getByRole('button',{name:'Make icons larger'}).count()) throw new Error('Legacy enlargement control remains');
    if(i%3===0) await page.getByRole('button',{name:'I cannot identify it',exact:true}).click();
    else { await page.getByRole('button',{name:'Candidate 1',exact:true}).dblclick(); await page.waitForTimeout(180); await page.keyboard.press('4'); }
    if(progress.startsWith('Practice')) { await page.getByRole('button',{name:'Continue',exact:true}).waitFor(); await page.getByRole('button',{name:'Continue',exact:true}).click(); }
    else {
      await page.waitForFunction(()=>document.querySelector('#ready')||document.querySelector('#finish'));
      if((await page.locator('#content').textContent()).includes('not the target') || (await page.locator('#content').textContent()).includes('Correct.')) throw new Error('Recorded feedback leaked');
    }
  }
}
