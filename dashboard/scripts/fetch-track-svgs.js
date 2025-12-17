#!/usr/bin/env node
/**
 * Fetch Accurate Track SVGs from Wikimedia Commons
 * Downloads official track layout SVGs and extracts path data
 * 
 * Usage: node scripts/fetch-track-svgs.js
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Wikimedia Commons SVG URLs for accurate track layouts
// These are the raw file URLs from Wikimedia
const TRACK_SOURCES = {
    'Silverstone': 'https://upload.wikimedia.org/wikipedia/commons/b/bd/Silverstone_Circuit_2020.svg',
    'Spa': 'https://upload.wikimedia.org/wikipedia/commons/5/54/Spa-Francorchamps_of_Belgium.svg',
    'Monza': 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Monza_track_map.svg',
    'Suzuka': 'https://upload.wikimedia.org/wikipedia/commons/e/ec/Suzuka_circuit_map--2005.svg',
    'RedBullRing': 'https://upload.wikimedia.org/wikipedia/commons/b/b2/Circuit_Red_Bull_Ring.svg',
    'Interlagos': 'https://upload.wikimedia.org/wikipedia/commons/4/41/Aut%C3%B3dromo_Jos%C3%A9_Carlos_Pace_%28AKA_Interlagos%29_track_map.svg',
    'Daytona': 'https://upload.wikimedia.org/wikipedia/commons/b/b4/Daytona_International_Speedway_-_Road_Course.svg',
    'Nurburgring': 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Nurburgring_-_Grand-Prix-Strecke.svg',
    'Laguna': 'https://upload.wikimedia.org/wikipedia/commons/3/34/WeatherTech_Raceway_Laguna_Seca_track_map.svg'
};

const OUTPUT_DIR = path.join(__dirname, '..', 'src', 'data', 'tracks', 'svg');

// Create output directory
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

/**
 * Fetch SVG from URL with proper headers
 */
function fetchSVG(url) {
    return new Promise((resolve, reject) => {
        const options = {
            headers: {
                'User-Agent': 'PitBox Dashboard/1.0 (https://github.com/pitbox; contact@pitbox.app) Node.js',
                'Accept': 'image/svg+xml,*/*',
            }
        };

        https.get(url, options, (response) => {
            // Handle redirects
            if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
                fetchSVG(response.headers.location).then(resolve).catch(reject);
                return;
            }

            if (response.statusCode !== 200) {
                reject(new Error(`HTTP ${response.statusCode}`));
                return;
            }

            let data = '';
            response.on('data', chunk => data += chunk);
            response.on('end', () => resolve(data));
            response.on('error', reject);
        }).on('error', reject);
    });
}

/**
 * Extract path 'd' attribute from SVG content
 */
function extractPaths(svgContent, trackName) {
    // Simple regex to find path elements and their d attributes
    const pathRegex = /<path[^>]*\sd="([^"]+)"[^>]*>/gi;
    const paths = [];
    let match;

    while ((match = pathRegex.exec(svgContent)) !== null) {
        paths.push(match[1]);
    }

    // Find viewBox
    const viewBoxMatch = svgContent.match(/viewBox="([^"]+)"/i);
    const viewBox = viewBoxMatch ? viewBoxMatch[1] : '0 0 1000 1000';

    console.log(`  Found ${paths.length} paths, viewBox: ${viewBox}`);

    return { paths, viewBox };
}

/**
 * Download and process all tracks
 */
async function main() {
    console.log('🏎️  Fetching Accurate Track SVGs from Wikimedia Commons\n');

    const results = {};

    for (const [trackName, url] of Object.entries(TRACK_SOURCES)) {
        console.log(`Fetching ${trackName}...`);
        try {
            const svgContent = await fetchSVG(url);

            // Save raw SVG
            const filename = `${trackName.toLowerCase().replace(/\s+/g, '_')}.svg`;
            fs.writeFileSync(path.join(OUTPUT_DIR, filename), svgContent);
            console.log(`  ✅ Saved ${filename}`);

            // Extract path data
            const { paths, viewBox } = extractPaths(svgContent, trackName);
            results[trackName] = { viewBox, pathCount: paths.length, mainPath: paths[0] };

        } catch (error) {
            console.log(`  ❌ Failed: ${error.message}`);
            results[trackName] = { error: error.message };
        }
    }

    // Save extracted data summary
    const summaryPath = path.join(OUTPUT_DIR, 'paths.json');
    fs.writeFileSync(summaryPath, JSON.stringify(results, null, 2));
    console.log(`\n📝 Saved path summary to ${summaryPath}`);

    console.log('\n✅ Done! Check the svg/ directory for downloaded files.');
}

main().catch(console.error);
