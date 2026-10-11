// Playwright CLI run-code snippet for an unused invitation tab at the introduction.
async (page) => {
  await page.route('**/normalized_256/**',route=>route.abort());
  await page.reload();
  await page.getByRole('button',{name:'Retry',exact:true}).waitFor();
  if(await page.getByRole('button',{name:'Begin anonymous session'}).count()) throw new Error('Missing images did not block start');
  await page.unroute('**/normalized_256/**');
  await page.getByRole('button',{name:'Retry',exact:true}).click();
  await page.getByRole('button',{name:'Begin anonymous session'}).waitFor();
  await page.setViewportSize({width:600,height:700});
  await page.getByRole('button',{name:'Begin anonymous session'}).click();
  await page.getByRole('heading',{name:'Pilot paused'}).waitFor();
  await page.locator('#endPaused').click();
  await page.getByText('Session ended. Completed responses are saved.',{exact:true}).waitFor();
}
