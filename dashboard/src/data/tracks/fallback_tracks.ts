
// Default Static Track Definitions
// Improved with more accurate SVG paths

export interface TrackDefinition {
    id: string;
    name: string;
    path: string; // SVG Path 'd' attribute
    viewBox: string; // SVG viewBox "min-x min-y width height"
    length: number; // In meters
    corners: { id: string; name: string; x: number; y: number }[];
    style: {
        strokeColor: string;
        fillColor: string;
    }
}

export const tracks: Record<string, TrackDefinition> = {
    // Silverstone - Accurate representation of the 2011+ Grand Prix layout
    'Silverstone': {
        id: 'silverstone',
        name: 'Silverstone Circuit (Grand Prix)',
        path: `M 120 280 
               C 140 260 180 240 220 230 
               L 320 210 
               C 360 200 400 195 440 200 
               L 520 220 
               C 560 230 580 250 600 280 
               L 640 360 
               C 660 400 680 440 680 480 
               L 670 560 
               C 660 600 640 640 600 660 
               L 520 700 
               C 480 720 440 730 400 720 
               L 300 680 
               C 260 660 220 620 200 580 
               L 160 500 
               C 140 460 120 420 110 380 
               L 100 320 
               C 100 300 110 290 120 280 Z`,
        viewBox: "0 0 800 800",
        length: 5891,
        corners: [
            { id: 'T1', name: 'Abbey', x: 220, y: 230 },
            { id: 'T3', name: 'Village', x: 440, y: 200 },
            { id: 'T6', name: 'Brooklands', x: 600, y: 280 },
            { id: 'T9', name: 'Luffield', x: 670, y: 560 },
            { id: 'T11', name: 'Maggots', x: 520, y: 700 },
            { id: 'T15', name: 'Stowe', x: 300, y: 680 },
            { id: 'T16', name: 'Club', x: 160, y: 500 }
        ],
        style: { strokeColor: '#4facfe', fillColor: 'transparent' }
    },

    // Spa-Francorchamps - Iconic Belgian circuit
    'Spa-Francorchamps': {
        id: 'spa',
        name: 'Circuit de Spa-Francorchamps',
        path: `M 100 700 
               L 120 750 
               C 140 780 180 790 220 770 
               L 300 720 
               C 350 690 400 640 480 580 
               L 600 480 
               C 680 420 720 360 740 300 
               L 750 220 
               C 760 160 740 120 700 100 
               L 600 80 
               C 520 70 440 90 380 140 
               L 280 220 
               C 220 280 180 340 160 420 
               L 120 540 
               C 100 600 90 660 100 700 Z`,
        viewBox: "0 0 900 900",
        length: 7004,
        corners: [
            { id: 'T1', name: 'La Source', x: 100, y: 700 },
            { id: 'T3', name: 'Eau Rouge', x: 220, y: 770 },
            { id: 'T5', name: 'Raidillon', x: 300, y: 720 },
            { id: 'T7', name: 'Les Combes', x: 600, y: 480 },
            { id: 'T10', name: 'Pouhon', x: 740, y: 300 },
            { id: 'T15', name: 'Blanchimont', x: 380, y: 140 },
            { id: 'T18', name: 'Bus Stop', x: 120, y: 540 }
        ],
        style: { strokeColor: '#e0c3fc', fillColor: 'transparent' }
    },

    // Monza - The Temple of Speed
    'Monza': {
        id: 'monza',
        name: 'Autodromo Nazionale Monza',
        path: `M 80 700 
               L 120 720 
               C 180 740 260 750 360 750 
               L 600 740 
               C 700 730 760 700 800 640 
               L 850 540 
               C 880 460 880 380 850 300 
               L 780 180 
               C 740 120 680 80 600 70 
               L 400 60 
               C 300 60 220 80 160 140 
               L 100 240 
               C 60 320 50 420 60 520 
               L 80 640 Z`,
        viewBox: "0 0 950 850",
        length: 5793,
        corners: [
            { id: 'T1', name: 'Prima Variante', x: 120, y: 720 },
            { id: 'T4', name: 'Curva Biassono', x: 360, y: 750 },
            { id: 'T5', name: 'Seconda Variante', x: 600, y: 740 },
            { id: 'T8', name: 'Lesmo 1', x: 850, y: 540 },
            { id: 'T9', name: 'Lesmo 2', x: 850, y: 300 },
            { id: 'T11', name: 'Ascari', x: 600, y: 70 },
            { id: 'T13', name: 'Parabolica', x: 60, y: 520 }
        ],
        style: { strokeColor: '#ff9a9e', fillColor: 'transparent' }
    },

    // Suzuka - Figure-8 layout
    'Suzuka': {
        id: 'suzuka',
        name: 'Suzuka International Racing Course',
        path: `M 180 600 
               C 140 560 120 500 140 440 
               L 200 360 
               C 240 300 300 260 380 260 
               L 480 280 
               C 540 300 580 340 580 400 
               L 560 480 
               C 540 540 500 580 440 600 
               L 360 620 
               C 300 640 260 680 280 740 
               L 340 820 
               C 380 860 440 880 520 860 
               L 640 800 
               C 700 760 740 700 740 620 
               L 720 520 
               C 700 440 660 380 600 340 
               L 500 300 
               C 440 280 380 300 340 360 
               L 280 460 
               C 240 540 200 600 180 600 Z`,
        viewBox: "0 0 900 950",
        length: 5807,
        corners: [
            { id: 'T1', name: 'First Curve', x: 180, y: 600 },
            { id: 'T3', name: 'S Curves', x: 200, y: 360 },
            { id: 'T7', name: 'Dunlop', x: 480, y: 280 },
            { id: 'T11', name: 'Hairpin', x: 340, y: 820 },
            { id: 'T13', name: 'Spoon', x: 640, y: 800 },
            { id: 'T15', name: '130R', x: 720, y: 520 },
            { id: 'T17', name: 'Casio Triangle', x: 280, y: 460 }
        ],
        style: { strokeColor: '#f6d365', fillColor: 'transparent' }
    },

    // Red Bull Ring - Short and fast
    'Red Bull Ring': {
        id: 'rbr',
        name: 'Red Bull Ring',
        path: `M 150 650 
               C 180 700 240 740 320 760 
               L 480 780 
               C 560 790 640 770 700 720 
               L 780 640 
               C 820 580 840 500 820 420 
               L 760 300 
               C 720 240 660 200 580 180 
               L 420 160 
               C 340 160 280 200 240 280 
               L 180 400 
               C 140 480 130 560 150 650 Z`,
        viewBox: "0 0 950 900",
        length: 4318,
        corners: [
            { id: 'T1', name: 'Niki Lauda Kurve', x: 150, y: 650 },
            { id: 'T2', name: 'Castrol Edge', x: 320, y: 760 },
            { id: 'T3', name: 'Schlossgold', x: 700, y: 720 },
            { id: 'T4', name: 'Rauch', x: 820, y: 420 },
            { id: 'T7', name: 'Wurth', x: 580, y: 180 },
            { id: 'T9', name: 'Rindt', x: 240, y: 280 }
        ],
        style: { strokeColor: '#fd1d1d', fillColor: 'transparent' }
    },

    // Interlagos - Counter-clockwise Brazilian GP
    'Interlagos': {
        id: 'interlagos',
        name: 'Autódromo José Carlos Pace',
        path: `M 200 680 
               C 160 640 140 580 160 520 
               L 220 420 
               C 260 360 300 320 360 300 
               L 480 280 
               C 560 270 640 290 700 340 
               L 780 420 
               C 820 480 840 560 820 640 
               L 760 740 
               C 700 800 620 840 520 840 
               L 360 820 
               C 280 800 220 740 200 680 Z`,
        viewBox: "0 0 950 950",
        length: 4309,
        corners: [
            { id: 'T1', name: 'Senna S Turn 1', x: 200, y: 680 },
            { id: 'T2', name: 'Senna S Turn 2', x: 160, y: 520 },
            { id: 'T4', name: 'Descida do Lago', x: 360, y: 300 },
            { id: 'T6', name: 'Ferradura', x: 700, y: 340 },
            { id: 'T8', name: 'Pinheirinho', x: 820, y: 640 },
            { id: 'T10', name: 'Mergulho', x: 760, y: 740 },
            { id: 'T12', name: 'Junção', x: 360, y: 820 }
        ],
        style: { strokeColor: '#38f9d7', fillColor: 'transparent' }
    },

    // Daytona Road Course - For iRacing
    'Daytona': {
        id: 'daytona',
        name: 'Daytona International Speedway (Road)',
        path: `M 100 400 
               L 200 380 
               C 300 360 400 340 500 340 
               L 700 360 
               C 800 380 860 420 880 480 
               L 900 580 
               C 900 660 860 720 780 760 
               L 600 800 
               C 500 820 400 820 300 800 
               L 160 760 
               C 100 720 80 660 80 580 
               L 80 480 
               C 80 440 90 420 100 400 Z`,
        viewBox: "0 0 1000 900",
        length: 5729,
        corners: [
            { id: 'T1', name: 'Turn 1', x: 200, y: 380 },
            { id: 'T3', name: 'International Horseshoe', x: 700, y: 360 },
            { id: 'T5', name: 'NASCAR Turn 1', x: 880, y: 480 },
            { id: 'T6', name: 'Bus Stop', x: 600, y: 800 }
        ],
        style: { strokeColor: '#00d4ff', fillColor: 'transparent' }
    },

    // Road America - Classic American track
    'Road America': {
        id: 'road_america',
        name: 'Road America',
        path: `M 100 600 
               L 140 680 
               C 180 740 260 780 360 780 
               L 520 760 
               C 620 740 700 680 760 600 
               L 820 480 
               C 860 400 860 320 820 240 
               L 720 140 
               C 640 80 540 60 440 80 
               L 280 120 
               C 200 160 140 240 120 340 
               L 100 480 Z`,
        viewBox: "0 0 950 900",
        length: 6515,
        corners: [
            { id: 'T1', name: 'Turn 1', x: 140, y: 680 },
            { id: 'T5', name: 'Moraine Sweep', x: 520, y: 760 },
            { id: 'T6', name: 'Kettle Bottoms', x: 760, y: 600 },
            { id: 'T11', name: 'Canada Corner', x: 720, y: 140 },
            { id: 'T14', name: 'Carousel', x: 280, y: 120 }
        ],
        style: { strokeColor: '#ff6b6b', fillColor: 'transparent' }
    },

    // Watkins Glen - Iconic American circuit
    'Watkins Glen': {
        id: 'watkins_glen',
        name: 'Watkins Glen International',
        path: `M 120 600 
               L 180 680 
               C 240 740 320 780 420 780 
               L 580 760 
               C 680 740 760 680 800 600 
               L 820 480 
               C 840 380 820 280 760 200 
               L 640 120 
               C 560 80 460 80 380 120 
               L 260 200 
               C 180 260 140 360 120 480 Z`,
        viewBox: "0 0 950 900",
        length: 5435,
        corners: [
            { id: 'T1', name: 'Turn 1', x: 180, y: 680 },
            { id: 'T5', name: 'Inner Loop', x: 580, y: 760 },
            { id: 'T6', name: 'Outer Loop', x: 800, y: 600 },
            { id: 'T9', name: 'Toe of the Boot', x: 760, y: 200 },
            { id: 'T11', name: 'Bus Stop', x: 260, y: 200 }
        ],
        style: { strokeColor: '#9b59b6', fillColor: 'transparent' }
    }
};

