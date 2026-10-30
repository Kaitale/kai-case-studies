// Print paper.html and technical_report.html (from build_documents.py) to A4 PDF with page numbers.
// Usage: node print.js [folder]   (needs Playwright; set CHROME_PATH to use a specific Chromium)
const { chromium } = require('playwright');
const dir = require('path').resolve(process.argv[2] || __dirname);
(async () => {
  const b = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
  for (const [src, out, title] of [['paper.html', 'paper.pdf', 'Kakooza (2026) · River flow or rainfall? Parametric flood triggers from global data'], ['technical_report.html', 'technical_report.pdf', 'KAI-Hydro technical report KH-TR-2026-01']]) {
    const p = await b.newPage();
    await p.goto('file://' + dir + '/' + src, { waitUntil: 'load' });
    await p.pdf({ path: dir + '/' + out, format: 'A4', printBackground: true, margin: { top: '18mm', bottom: '18mm', left: '18mm', right: '18mm' },
      displayHeaderFooter: true, headerTemplate: '<span></span>',
      footerTemplate: `<div style="width:100%;font-family:Inter,sans-serif;font-size:7.5px;color:#666;padding:0 18mm;display:flex;justify-content:space-between"><span>${title}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>` });
    await p.close();
  }
  await b.close();
})();
