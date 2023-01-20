// https://github.com/bpmn-io/bpmn-to-image
const {
  basename,
  relative,
  resolve
} = require('path');

const {
  readFileSync
} = require('fs');

const fs = require('fs');

require('./puppeteer.production.min.js');

async function printDiagram(page, options) {

  const {
    input,
    outputs,
    minDimensions,
    footer,
    title = true,
    deviceScaleFactor
  } = options;

  const diagramXML = readFileSync(input, 'utf8');

  const diagramTitle = title === false ? false : (
    title.length ? title : basename(input)
  );

  await page.goto(`file://${__dirname}/skeleton.html`);

  const viewerScript = relative(__dirname, require.resolve('./bpmn-viewer.production.min.js'));

  const desiredViewport = await page.evaluate(async function(diagramXML, options) {

    const {
      viewerScript,
      ...openOptions
    } = options;

    await loadScript(viewerScript);

    // returns desired viewport
    return openDiagram(diagramXML, openOptions);
  }, diagramXML, {
    minDimensions,
    title: diagramTitle,
    viewerScript,
    footer
  });;

  page.setViewport({
    width: Math.round(desiredViewport.width),
    height: Math.round(desiredViewport.height),
    deviceScaleFactor: deviceScaleFactor
  });

  await page.evaluate(() => resize());

  for (const output of outputs) {

    if (output.endsWith('.pdf')) {
      await page.pdf({
        path: output,
        width: desiredViewport.width,
        height: desiredViewport.diagramHeight
      });
    } else
    if (output.endsWith('.png')) {
      await page.screenshot({
        path: output,
        clip: {
          x: 0,
          y: 0,
          width: desiredViewport.width,
          height: desiredViewport.diagramHeight
        }
      });
    } else
    if (output.endsWith('.svg')) {

      const svg = await page.evaluate(() => toSVG());

      fs.writeFileSync(output, svg, 'utf8');
    } else {
      console.error(`Unknown output file format: ${output}`);
    }
  }

}


async function withPage(fn) {
  let browser;

  try {
    browser = await puppeteer.launch({executablePath: process.env.PUPPETEER_EXECUTABLE_PATH});
    await fn(await browser.newPage());
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}


async function convertAll(conversions, options={}) {

  const {
    minDimensions,
    footer,
    title,
    deviceScaleFactor
  } = options;

  await withPage(async function(page) {

    for (const conversion of conversions) {

      const {
        input,
        outputs
      } = conversion;

      await printDiagram(page, {
        input,
        outputs,
        minDimensions,
        title,
        footer,
        deviceScaleFactor
      });
    }

  });

}

async function convert(input, output) {
  return await convertAll([
    {
      input,
      outputs: [ output ]
    }
  ]);
}

// PNG is required for capturing HTML annotations outside SVG layer
convert(resolve(__dirname, "input.bpmn"), resolve(__dirname, "output.png"));

