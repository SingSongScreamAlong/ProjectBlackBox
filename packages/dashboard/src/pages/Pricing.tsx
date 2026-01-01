/**
 * Pricing Page - v1 Commercial Model
 * 
 * AUTHORITATIVE PRICING:
 * - BlackBox: $16/month per driver
 * - ControlBox: $18/month per league + $2/series
 * - RaceBox: FREE (baseline, branding required)
 * - RaceBox Plus: $15/month per league + $2/series
 */

import { useNavigate, useSearchParams } from 'react-router-dom';
import { useBootstrap } from '../hooks/useBootstrap';
import './Pricing.css';

// Squarespace checkout URLs
const CHECKOUT_URLS = {
    blackbox: 'https://okboxbox.squarespace.com/checkout/blackbox-monthly',
    controlbox: 'https://okboxbox.squarespace.com/checkout/controlbox-monthly',
    racebox_plus: 'https://okboxbox.squarespace.com/checkout/racebox-plus-monthly',
};

const RETURN_URL = typeof window !== 'undefined'
    ? `${window.location.origin}/billing/return`
    : '/billing/return';

interface PricingTier {
    id: string;
    name: string;
    tagline: string;
    description: string;
    basePrice: number;
    priceUnit: string;
    seriesAddon?: number;
    features: string[];
    popular?: boolean;
    free?: boolean;
    ctaText: string;
    ctaAction?: 'checkout' | 'navigate';
    ctaTarget?: string;
}

const PRICING_TIERS: PricingTier[] = [
    {
        id: 'racebox',
        name: 'RaceBox',
        tagline: 'Free for Everyone',
        description: 'Basic broadcast tools for leagues, streamers, and spectators.',
        basePrice: 0,
        priceUnit: 'forever free',
        free: true,
        features: [
            'Public timing pages',
            'Basic timing tower overlay',
            'Basic broadcast overlays',
            'Ok, Box Box branding included'
        ],
        ctaText: 'Start Broadcasting',
        ctaAction: 'navigate',
        ctaTarget: '/watch/demo'
    },
    {
        id: 'blackbox',
        name: 'BlackBox',
        tagline: 'For Drivers & Teams',
        description: 'Live race execution and situational awareness for competitive drivers.',
        basePrice: 16,
        priceUnit: 'per driver',
        features: [
            'Live situational awareness',
            'Team coordination surface',
            'Replay and forensics',
            'Gap and delta tracking',
            'Fuel and tire strategy',
            'Opponent intel'
        ],
        ctaText: 'Start Racing',
        ctaAction: 'checkout'
    },
    {
        id: 'controlbox',
        name: 'ControlBox',
        tagline: 'For Leagues',
        description: 'Race control automation and steward workflows for league operations.',
        basePrice: 18,
        priceUnit: 'per league',
        seriesAddon: 2,
        popular: true,
        features: [
            'Race control automation',
            'Incident detection & workflows',
            'Rulebook enforcement',
            'Steward forensics',
            'League & series management',
            'Audit logging'
        ],
        ctaText: 'Run Your League',
        ctaAction: 'checkout'
    },
    {
        id: 'racebox_plus',
        name: 'RaceBox Plus',
        tagline: 'Professional Broadcast',
        description: 'Advanced broadcast features for monetized and professional streams.',
        basePrice: 15,
        priceUnit: 'per league',
        seriesAddon: 2,
        features: [
            'Director control panel',
            'Scene presets',
            'Battle box overlays',
            'Incident banners',
            'Delay buffer controls',
            'League branding',
            'Sponsor logo slots'
        ],
        ctaText: 'Go Professional',
        ctaAction: 'checkout'
    }
];

export function Pricing() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { bootstrap, hasLicense } = useBootstrap();

    const intent = searchParams.get('intent');

    const handleCheckout = (product: string) => {
        const baseUrl = CHECKOUT_URLS[product as keyof typeof CHECKOUT_URLS];
        if (!baseUrl) return;
        const checkoutUrl = `${baseUrl}?onsuccess=${encodeURIComponent(RETURN_URL)}&email=${encodeURIComponent(bootstrap?.user.email || '')}`;
        window.location.href = checkoutUrl;
    };

    const handleCta = (tier: PricingTier) => {
        if (tier.ctaAction === 'navigate' && tier.ctaTarget) {
            navigate(tier.ctaTarget);
        } else {
            handleCheckout(tier.id);
        }
    };

    return (
        <div className="pricing-page">
            <header className="pricing-header">
                <h1>Simple, Transparent Pricing</h1>
                <p>Live race execution. Situational awareness. Broadcast presentation.</p>
                {intent && (
                    <p className="intent-notice">
                        Subscribe to unlock <strong>{intent}</strong> features
                    </p>
                )}
            </header>

            <div className="pricing-grid">
                {PRICING_TIERS.map(tier => {
                    const owned = tier.free
                        ? false
                        : hasLicense(tier.id as 'blackbox' | 'controlbox');

                    return (
                        <div
                            key={tier.id}
                            className={`pricing-card ${tier.popular ? 'popular' : ''} ${tier.free ? 'free' : ''} ${owned ? 'owned' : ''}`}
                        >
                            {tier.popular && <span className="popular-badge">Most Popular</span>}
                            {tier.free && <span className="free-badge">FREE</span>}
                            {owned && <span className="owned-badge">✓ Active</span>}

                            <div className="tier-header">
                                <span className="tier-tagline">{tier.tagline}</span>
                                <h2>{tier.name}</h2>
                            </div>

                            <p className="tier-description">{tier.description}</p>

                            <div className="pricing-amount">
                                {tier.free ? (
                                    <span className="price-free">$0</span>
                                ) : (
                                    <>
                                        <span className="currency">$</span>
                                        <span className="price">{tier.basePrice}</span>
                                        <span className="period">/month</span>
                                    </>
                                )}
                            </div>
                            <p className="price-unit">{tier.priceUnit}</p>

                            {tier.seriesAddon && (
                                <p className="series-addon">
                                    + ${tier.seriesAddon}/month per additional series
                                </p>
                            )}

                            <ul className="features">
                                {tier.features.map((feature, i) => (
                                    <li key={i}>✓ {feature}</li>
                                ))}
                            </ul>

                            {owned ? (
                                <button className="subscribe-btn owned" disabled>
                                    Already Subscribed
                                </button>
                            ) : (
                                <button
                                    className="subscribe-btn"
                                    onClick={() => handleCta(tier)}
                                >
                                    {tier.ctaText}
                                </button>
                            )}
                        </div>
                    );
                })}
            </div>

            <section className="pricing-notes">
                <h3>How It Works</h3>
                <div className="notes-grid">
                    <div className="note">
                        <span className="note-icon">📺</span>
                        <h4>RaceBox (Free)</h4>
                        <p>Basic overlays for anyone. Ok, Box Box branding required.</p>
                    </div>
                    <div className="note">
                        <span className="note-icon">👤</span>
                        <h4>BlackBox</h4>
                        <p>Billed per driver. Each team member needs their own license.</p>
                    </div>
                    <div className="note">
                        <span className="note-icon">🏁</span>
                        <h4>ControlBox</h4>
                        <p>Billed per league. Add series for $2/month each.</p>
                    </div>
                    <div className="note">
                        <span className="note-icon">🎬</span>
                        <h4>RaceBox Plus</h4>
                        <p>For professional streams. Drivers never pay.</p>
                    </div>
                </div>
            </section>

            <footer className="pricing-footer">
                <p>All paid plans include a 7-day free trial. Cancel anytime.</p>
                <button onClick={() => navigate('/home')} className="back-link">
                    ← Back to Launchpad
                </button>
            </footer>
        </div>
    );
}

export default Pricing;
