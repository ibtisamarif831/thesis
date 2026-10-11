// Playwright CLI run-code: start at an unused controlled invitation introduction.
async (page) => {
  await page.setViewportSize({width:1280,height:900});
  await page.bringToFront();
  await page.getByRole('button',{name:'Begin anonymous session',exact:true}).click();
  await page.getByRole('button',{name:'Ready',exact:true}).waitFor();
  if(!(await page.locator('#status').textContent()).includes('Practice 1 of 3')) throw Error('Wrong practice progress');
  await page.getByRole('button',{name:'Ready',exact:true}).dblclick();
  await page.getByRole('button',{name:'Candidate 1',exact:true}).waitFor();
  if(await page.locator('.grid button').count()!==5 || await page.locator('#enlarge').count()) throw Error('Wrong options or legacy controls');
  const boxes=await page.locator('.grid button').evaluateAll(nodes=>nodes.map(n=>({top:n.getBoundingClientRect().top,width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height})));
  if(new Set(boxes.map(b=>b.top)).size!==1 || boxes.some(b=>b.width!==112 || b.height!==112)) throw Error('Not one fixed-size row');
  if(await page.locator('.grid img').first().evaluate(n=>n.width)!==14) throw Error('Wrong practice size');
  // Failed acknowledgment + refresh must preserve exactly the pending answer.
  await page.route('**/api/pilot-trials',route=>route.request().postDataJSON()?.action==='answer'?route.abort():route.continue());
  await page.keyboard.press('1');
  await page.waitForTimeout(180);await page.keyboard.press('4');
  await page.getByRole('button',{name:'Retry',exact:true}).waitFor();
  await page.reload();await page.getByRole('button',{name:'Retry',exact:true}).waitFor();
  await page.unroute('**/api/pilot-trials');
  await page.getByRole('button',{name:'Retry',exact:true}).click();
  await page.getByRole('button',{name:'Continue',exact:true}).waitFor();await page.getByRole('button',{name:'Continue',exact:true}).click();
  // A held key during target exposure must not answer or enter confidence.
  await page.getByRole('button',{name:'Ready',exact:true}).click();
  await page.locator('.target').waitFor();await page.keyboard.down('1');
  await page.getByRole('button',{name:'Candidate 1',exact:true}).waitFor();await page.keyboard.down('1');
  if(await page.locator('.confidence').count()) throw Error('Held exposure key answered');
  await page.keyboard.up('1');await page.keyboard.down('1');await page.keyboard.down('1');
  if(await page.locator('.confidence').count()!==1) throw Error('Held choice key saved confidence');
  await page.keyboard.up('1');await page.waitForTimeout(180);await page.keyboard.press('5');
  await page.getByRole('button',{name:'Continue',exact:true}).waitFor();await page.getByRole('button',{name:'Continue',exact:true}).click();
  // Third practice via mouse.
  await page.getByRole('button',{name:'Ready',exact:true}).click();await page.getByRole('button',{name:'Candidate 2',exact:true}).waitFor();
  await page.getByRole('button',{name:'Candidate 2',exact:true}).click();await page.waitForTimeout(180);await page.getByRole('button',{name:'3',exact:true}).click();
  await page.getByRole('button',{name:'Continue',exact:true}).waitFor();await page.getByRole('button',{name:'Continue',exact:true}).click();
  if(!(await page.locator('#status').textContent()).includes('Recorded trial 1 of 100')) throw Error('Wrong recorded count');
  // Refresh retains target/size/options and marks repeated exposure.
  await page.getByRole('button',{name:'Ready',exact:true}).click();await page.getByRole('button',{name:'Candidate 1',exact:true}).waitFor();
  const before=await page.locator('.grid button').evaluateAll(nodes=>nodes.map(n=>[n.dataset.id,n.querySelector('img').width]));
  await page.reload();await page.getByRole('button',{name:'Ready',exact:true}).waitFor();
  await page.getByRole('button',{name:'Ready',exact:true}).click();await page.getByRole('button',{name:'Candidate 1',exact:true}).waitFor();
  const after=await page.locator('.grid button').evaluateAll(nodes=>nodes.map(n=>[n.dataset.id,n.querySelector('img').width]));
  if(JSON.stringify(before)!==JSON.stringify(after)) throw Error('Refresh changed assignment');
  await page.keyboard.press('2');await page.waitForTimeout(180);await page.keyboard.press('4');
  await page.getByRole('button',{name:'Ready',exact:true}).waitFor();
  if((await page.locator('#content').textContent()).includes('Correct.') || (await page.locator('#content').textContent()).includes('not the target')) throw Error('Recorded correctness leaked');
  await page.getByRole('button',{name:'Ready',exact:true}).click();await page.getByRole('button',{name:'I cannot identify it',exact:true}).waitFor();
  await page.getByRole('button',{name:'I cannot identify it',exact:true}).click();await page.getByRole('button',{name:'Ready',exact:true}).waitFor();
  await page.setViewportSize({width:600,height:500});await page.getByRole('heading',{name:'Pilot paused',exact:true}).waitFor();
  await page.locator('#endPaused').click();await page.getByText('Session ended. Completed responses are saved.',{exact:true}).waitFor();
  console.log('PASS: five-option row, 14px practice, progress, keyboard/repeat lock, mouse input, offline+refresh retry, stable interrupted assignments, no recorded feedback, unidentified and paused early exit.');
}
