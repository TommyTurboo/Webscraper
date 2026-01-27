const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'Schneider Arrayµ.txt');

try {
  const raw = fs.readFileSync(filePath, 'utf8');

  // Zoek attribute plain-all-data="..."`
  const key = 'plain-all-data="';
  const start = raw.indexOf(key);
  if (start === -1) {
    console.error('plain-all-data attribute niet gevonden in bestand');
    process.exit(1);
  }
  const afterStart = start + key.length;
  const endMarker = '" plain-product-id=';
  const end = raw.indexOf(endMarker, afterStart);
  if (end === -1) {
    console.error('eindmarker voor plain-all-data niet gevonden');
    process.exit(1);
  }

  let attr = raw.substring(afterStart, end);

  // HTML entities terugzetten naar normale quotes
  attr = attr.replace(/&quot;/g, '"');

  // JSON parsen
  const data = JSON.parse(attr);

  // Toon alleen specifications (of fallback)
  console.log('Gevonden productId:', data.productId || data.productCR || 'onbekend');
  console.log('specifications:', JSON.stringify(data.specifications, null, 2));
} catch (err) {
  console.error('Fout:', err.message);
  process.exit(1);
}