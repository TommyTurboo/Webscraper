const puppeteer = require('puppeteer');
const fs = require('fs');

async function scrapeSiemensProduct(url) {
    console.log(`⏳ Scraping: ${url}`);
    
    const browser = await puppeteer.launch({
        headless: false,
        args: ['--no-sandbox', '--start-maximized']
    });

    let page;

    try {
        page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });
        
        console.log('📄 Loading page...');
        await page.goto(url, { 
            waitUntil: 'networkidle2',
            timeout: 60000 
        });

        await new Promise(resolve => setTimeout(resolve, 3000));

        // 🍪 Cookies
        console.log('🍪 Accepting cookies...');
        try {
            await page.click('button[data-testid="uc-accept-all-button"]');
        } catch (e) {
            console.log('ℹ️  Cookie popup already closed');
        }
        
        await new Promise(resolve => setTimeout(resolve, 3000));

        // ⏳ Wait for component
        await page.waitForSelector('sie-ps-commercial-data', { timeout: 30000 });

        // 📜 Scroll
        console.log('📜 Scrolling...');
        await page.evaluate(async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= document.body.scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        });

        await new Promise(resolve => setTimeout(resolve, 5000));

        // 📊 SCRAPE - Met BEIDE section types
        console.log('\n🎯 Scraping ALL sections...');
        const specifications = await page.evaluate(() => {
            const data = {};
            
            const cleanText = (text) => {
                return text.replace(/\s+/g, ' ').replace(/\n+/g, ' ').trim();
            };
            
            // 1️⃣ Normale sections (.commercial-data-section)
            const normalSections = document.querySelectorAll('.commercial-data-section');
            
            normalSections.forEach(section => {
                const titleElem = section.querySelector('.commercial-data-section__title');
                const sectionTitle = titleElem ? cleanText(titleElem.textContent) : 'General';
                
                if (!data[sectionTitle]) {
                    data[sectionTitle] = {};
                }
                
                const items = section.querySelectorAll('ul li');
                
                items.forEach(item => {
                    const subtitle = item.querySelector('.commercial-data-section__subtitle');
                    
                    if (subtitle) {
                        const key = cleanText(subtitle.textContent);
                        const valueParagraph = item.querySelector('p:not(.commercial-data-section__subtitle)');
                        const valueDiv = item.querySelector('div > p');
                        const valueLink = item.querySelector('a');
                        
                        let value = '';
                        if (valueLink) {
                            value = cleanText(valueLink.textContent);
                        } else if (valueParagraph) {
                            value = cleanText(valueParagraph.textContent);
                        } else if (valueDiv) {
                            value = cleanText(valueDiv.textContent);
                        }
                        
                        if (key && value) {
                            data[sectionTitle][key] = value;
                        }
                    }
                });
            });
            
            // 2️⃣ TABLE sections (.commercial-data-table-section) - VOOR PRICING!
            const tableSections = document.querySelectorAll('.commercial-data-table-section');
            
            tableSections.forEach(section => {
                const titleElem = section.querySelector('.commercial-data-table-section__title');
                const sectionTitle = titleElem ? cleanText(titleElem.textContent) : 'Table Data';
                
                if (!data[sectionTitle]) {
                    data[sectionTitle] = {};
                }
                
                // Pricing data zit in een andere structuur
                const dataContainer = section.querySelector('.commercial-data-table-section-data');
                if (dataContainer) {
                    const items = dataContainer.querySelectorAll('.commercial-data-section__subtitle');
                    
                    items.forEach(subtitle => {
                        const key = cleanText(subtitle.textContent);
                        
                        // Zoek de value (kan in sibling zijn)
                        let valueElem = subtitle.nextElementSibling;
                        let value = '';
                        
                        if (valueElem && valueElem.tagName === 'P') {
                            value = cleanText(valueElem.textContent);
                        } else {
                            // Probeer parent > sibling
                            const parent = subtitle.parentElement;
                            if (parent) {
                                const valuePara = parent.querySelector('p:not(.commercial-data-section__subtitle)');
                                if (valuePara) {
                                    value = cleanText(valuePara.textContent);
                                }
                            }
                        }
                        
                        if (key) {
                            data[sectionTitle][key] = value || '–';
                        }
                    });
                }
            });
            
            // Verwijder lege secties
            Object.keys(data).forEach(section => {
                if (Object.keys(data[section]).length === 0) {
                    delete data[section];
                }
            });
            
            return data;
        });

        console.log('\n✅ Gevonden specificaties:');
        console.log(JSON.stringify(specifications, null, 2));

        // 💾 SAVE
        const output = {
            url,
            articleNumber: specifications['Product related']?.['Article number'] || 'unknown',
            scrapedAt: new Date().toISOString(),
            specifications,
            sectionsFound: Object.keys(specifications).length,
            dataFound: Object.keys(specifications).length > 0
        };

        fs.writeFileSync('siemens_data.json', JSON.stringify(output, null, 2));
        console.log(`\n💾 Opgeslagen: ${output.sectionsFound} secties in siemens_data.json`);

        await page.screenshot({ path: 'siemens_screenshot.png', fullPage: true });
        console.log('📸 Screenshot saved');

    } catch (error) {
        console.error('❌ Error:', error.message);
        
        if (page) {
            await page.screenshot({ path: 'error_screenshot.png', fullPage: true });
        }
        
    } finally {
        await browser.close();
    }
}

async function debugFullDOM(url) {
    console.log(`🔍 DEBUG: Full DOM inspection`);
    
    const browser = await puppeteer.launch({
        headless: false,
        args: ['--no-sandbox', '--start-maximized']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Accept cookies
        try {
            await page.click('button[data-testid="uc-accept-all-button"]');
            await new Promise(resolve => setTimeout(resolve, 3000));
        } catch (e) {}

        // Wait for component
        await page.waitForSelector('sie-ps-commercial-data', { timeout: 30000 });

        // Scroll
        await page.evaluate(async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= document.body.scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        });

        await new Promise(resolve => setTimeout(resolve, 5000));

        // 🔍 INSPECT: Wat ziet Puppeteer?
        const domAnalysis = await page.evaluate(() => {
            const analysis = {
                allClassesWithCommercial: [],
                allClassesWithPricing: [],
                allClassesWithClassification: [],
                allSections: [],
                allTabPanels: [],
                entireCommercialComponent: null
            };
            
            // Zoek alle elements met "commercial" in class
            document.querySelectorAll('[class*="commercial"]').forEach(el => {
                analysis.allClassesWithCommercial.push({
                    tag: el.tagName,
                    class: el.className,
                    text: el.textContent.substring(0, 100)
                });
            });
            
            // Zoek alle elements met "pricing" in class
            document.querySelectorAll('[class*="pricing"], [class*="price"]').forEach(el => {
                analysis.allClassesWithPricing.push({
                    tag: el.tagName,
                    class: el.className,
                    text: el.textContent.substring(0, 100)
                });
            });
            
            // Zoek alle elements met "classification" in class
            document.querySelectorAll('[class*="classification"]').forEach(el => {
                analysis.allClassesWithClassification.push({
                    tag: el.tagName,
                    class: el.className,
                    text: el.textContent.substring(0, 100)
                });
            });
            
            // Alle secties met title
            document.querySelectorAll('.commercial-data-section').forEach(section => {
                const title = section.querySelector('.commercial-data-section__title')?.textContent.trim();
                const itemCount = section.querySelectorAll('li').length;
                analysis.allSections.push({ title, itemCount });
            });
            
            // Zoek naar tab panels (misschien zit data in tabs?)
            document.querySelectorAll('[role="tabpanel"]').forEach((panel, i) => {
                analysis.allTabPanels.push({
                    index: i,
                    visible: panel.style.display !== 'none',
                    text: panel.textContent.substring(0, 200)
                });
            });
            
            // Pak de HELE sie-ps-commercial-data component
            const component = document.querySelector('sie-ps-commercial-data');
            if (component) {
                analysis.entireCommercialComponent = component.outerHTML.substring(0, 5000);
            }
            
            return analysis;
        });

        console.log('\n📊 DOM ANALYSIS:');
        console.log(JSON.stringify(domAnalysis, null, 2));
        
        // Save to file
        fs.writeFileSync('dom_analysis.json', JSON.stringify(domAnalysis, null, 2));
        console.log('\n💾 Saved to: dom_analysis.json');
        
        // Save FULL outerHTML zoals jij doet in DevTools
        const fullOuterHTML = await page.evaluate(() => {
            return document.documentElement.outerHTML;
        });
        
        fs.writeFileSync('full_outerhtml.html', fullOuterHTML);
        console.log('💾 Saved FULL outerHTML to: full_outerhtml.html');
        console.log('   Open dit bestand en zoek naar "Pricing" en "Classification"');

        console.log('\n👀 Browser blijft open - druk Ctrl+C om te stoppen');
        await new Promise(() => {});

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

const url = 'https://sieportal.siemens.com/en-be/products-services/detail/3RT2017-1HA41?tree=CatalogTree#overview';
scrapeSiemensProduct(url);