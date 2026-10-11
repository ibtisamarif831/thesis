// Playwright CLI run-code on a local pilot page. Mock API isolates keyboard tests from participant data.
async (rootPage) => {
  const base='http://127.0.0.1:8799';
  const catalog=await (await rootPage.request.get(base+'/study_selection_data.json')).json();
  const icons=catalog.sets[0].icons.slice(0,20).map(i=>({icon_id:i.icon_id,image:'/'+i.normalized_path}));
  for(const platform of ['Windows','macOS']) {
    const page=await rootPage.context().newPage();
    await page.addInitScript(value=>Object.defineProperty(navigator,'userAgentData',{value:{platform:value},configurable:true}),platform);
    let answers=0, attempts=[], ended=false, completed=false, failAnswer=true;
    const config={protocol_version:'icon-recognition-controlled-v2',icons,size_levels:[6,8,10,12,14],exposure_ms:1500,target_px:128,practice_count:1,recorded_count:2};
    const schedule=Array.from({length:3},(_,i)=>({phase:i?'recorded':'practice',trial_index:i,target_id:icons[i].icon_id,assigned_size:i?6:14,grid:icons.slice(0,5).map(x=>x.icon_id)}));
    await page.route('**/api/pilot-*',async route=>{
      const request=route.request(), url=request.url(), data=request.method()==='POST'?request.postDataJSON():null;
      let result;
      if(url.split('?')[0].endsWith('/api/pilot-sessions')) result=data?{session_id:'keyboard-fixture',credential:'test'}:url.includes('session_id=')?{config,schedule,next_trial:answers,status:'active',attempts}:{title:'Keyboard fixture',open:true,config};
      else if(url.split('?')[0].endsWith('/api/pilot-trials')) {
        if(data.action==='start') attempts.push({attempt_id:data.attempt_id,phase:schedule[answers].phase,state:'active',trial_index:answers});
        if(data.action==='answer') {
          if(failAnswer) {failAnswer=false;return route.abort();}
          const a=attempts.find(a=>a.attempt_id===data.attempt_id);a.state='answered';a.response=data.response;answers++;
        }
        result={ok:true,correct: schedule[Math.max(0,answers-1)].phase==='practice'?true:undefined};
      } else {completed=data.action==='complete';ended=data.action==='end';result={ok:true,status:completed?'completed':'ended'};}
      await route.fulfill({json:result});
    });
    await page.goto(base+'/pilot.html?pilot=keyboard-'+platform);await page.evaluate(()=>sessionStorage.clear());await page.reload();
    await page.setViewportSize({width:1280,height:900});await page.bringToFront();
    await page.getByRole('button',{name:'Begin anonymous session',exact:true}).waitFor();
    const enterLabel=platform==='macOS'?'Return ↵':'Enter ↵';
    if(await page.locator('#begin kbd').textContent()!==enterLabel)throw Error('Wrong platform key label');
    // Held Enter starts the session once but does not start the first exposure.
    await page.keyboard.down('Enter');await page.getByRole('button',{name:'Ready',exact:true}).waitFor();await page.keyboard.down('Enter');
    if(attempts.length)throw Error('Held Enter started a trial');await page.keyboard.up('Enter');
    for(let i=0;i<3;i++) {
      await page.keyboard.press('Enter');await page.getByRole('button',{name:'Candidate 1',exact:true}).waitFor();
      if(await page.locator('#unknown kbd').textContent()!=='0')throw Error('Unknown key badge missing');
      if(i===0) await page.screenshot({path:'output/playwright/keyboard-study-'+platform+'.png'});
      if(i===1)await page.keyboard.press('0');
      else {if(i===2) {await page.getByRole('button',{name:'Candidate 1',exact:true}).focus();await page.keyboard.press('Enter');} else await page.keyboard.press('1');await page.waitForTimeout(180); if(await page.getByRole('button',{name:'4',exact:true}).count()!==1)throw Error('Confidence accessible name missing'); await page.keyboard.press('4');}
      if(i===0) {
        await page.getByRole('button',{name:'Retry',exact:true}).waitFor();await page.keyboard.press('Enter');
        await page.getByRole('button',{name:'Continue',exact:true}).waitFor();await page.keyboard.press('Enter');
      } else if(i===1)await page.getByRole('button',{name:'Ready',exact:true}).waitFor();
    }
    await page.getByRole('button',{name:'Save and finish',exact:true}).waitFor();
    const modifier=platform==='macOS'?'Meta':'Control';
    if(!(await page.locator('#finish kbd').textContent()).includes(platform==='macOS'?'⌘':'Ctrl'))throw Error('Wrong finish badge');
    await page.locator('#difficulty').focus();await page.keyboard.type('12345 is text');await page.keyboard.press('Enter');await page.keyboard.type('0 remains text');
    if(completed || ended || !(await page.locator('#difficulty').inputValue()).includes('\n0 remains text'))throw Error('Reflection typing intercepted');
    await page.keyboard.press(modifier+'+Enter');await page.getByText('Session completed and saved.',{exact:true}).waitFor();
    if(!completed || answers!==3 || attempts.some(a=>a.response?.input_method!=='keyboard'))throw Error('Keyboard flow did not save correct telemetry');
    // Separate fresh session: platform-specific end shortcut, without mouse.
    answers=0;attempts=[];completed=false;ended=false;failAnswer=false;
    await page.evaluate(()=>sessionStorage.clear());await page.reload();await page.getByRole('button',{name:'Begin anonymous session',exact:true}).waitFor();await page.keyboard.press('Enter');
    await page.getByRole('button',{name:'Ready',exact:true}).waitFor();await page.setViewportSize({width:600,height:500});await page.getByRole('heading',{name:'Pilot paused',exact:true}).waitFor();
    if(platform==='Windows'){await page.locator('#endPaused').focus();await page.keyboard.press('Enter');}else await page.keyboard.press(modifier+'+Shift+X');await page.getByText('Session ended. Completed responses are saved.',{exact:true}).waitFor();
    if(!ended)throw Error('End shortcut failed');
    await page.unroute('**/api/pilot-*'); await page.close();
  }
}
