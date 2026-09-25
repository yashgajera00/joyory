import React, { useState, useRef, useEffect } from 'react';
import { SparklesIcon, ArrowRightIcon, BagIcon } from './Icons';
import { GridPulse } from '@/components/ui/grid-pulse';
import ReflectiveCard from './ReflectiveCard';
import DriftWall from './DriftWall';
import { formatRupees } from '@/lib/utils';
import { ALL_PRODUCTS } from '@/lib/productsData';
import { fetchProducts } from '../services/api';

function shuffleArray(array) {
  const arr = [...array];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}


function RecommendedProductCard({ rec, onSelectProduct, onAddToCart }) {
  const [adding, setAdding] = useState(false);

  const handleAdd = async (e) => {
    e.stopPropagation();
    if (!onAddToCart) return;
    setAdding(true);
    try {
      await onAddToCart(rec.product_id, 1);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div
      className="reco-product-card"
      onClick={() => onSelectProduct && onSelectProduct(rec.product_id)}
    >
      <div className="reco-card-badge-row">
        <span className="reco-category-pill">{rec.category || 'Skincare'}</span>
        <span className="reco-match-pill">
          <SparklesIcon size={12} />
          <span>AI Match</span>
        </span>
      </div>

      <div className="reco-product-image-box">
        <img
          src={rec.image_url || `/images/products/${rec.category_slug || 'moisturizer'}.jpg`}
          alt={rec.name}
          className="reco-product-img"
          loading="lazy"
          onError={(e) => {
            const fallback = `/images/products/${rec.category_slug || 'moisturizer'}.jpg`;
            if (!e.target.src.endsWith(fallback)) {
              e.target.src = fallback;
            }
          }}
        />
      </div>

      <div className="reco-product-body">
        <span className="reco-brand-label">{rec.brand || 'Joyory'}</span>
        <h3 className="reco-product-name">{rec.name}</h3>

        {rec.reason && (
          <div className="reco-reason-callout">
            <span className="reco-reason-icon">🎯</span>
            <p className="reco-reason-text">{rec.reason}</p>
          </div>
        )}

        <div className="reco-product-footer">
          <div className="reco-product-price">
            {formatRupees(rec.price)}
          </div>
          {onAddToCart && (
            <button
              className="btn-reco-add-bag"
              onClick={handleAdd}
              disabled={adding}
              id={`reco-add-${rec.product_id}`}
            >
              <BagIcon size={15} />
              <span>{adding ? 'Adding...' : 'Add to Bag'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const DEFAULT_RECOMMENDATIONS = [
  {
    product_id: 13,
    name: 'Joyory Pore Clarifying BHA Foaming Wash',
    category: 'Cleanser',
    category_slug: 'cleanser',
    price: '649.00',
    image_url: '/images/products/product_13.jpg',
    brand: 'Joyory',
    reason: 'Formulated with Salicylic Acid to clear congested pores and regulate excess sebum.',
  },
  {
    product_id: 32,
    name: 'Joyory Azelaic Acid 10% Calming Suspension',
    category: 'Serum',
    category_slug: 'serum',
    price: '899.00',
    image_url: '/images/products/product_32.jpg',
    brand: 'Joyory',
    reason: 'Multi-functional brightening booster that targets skin texture and redness.',
  },
  {
    product_id: 46,
    name: 'Joyory Niacinamide Oil-Free Mattifying Gel',
    category: 'Moisturizer',
    category_slug: 'moisturizer',
    price: '949.00',
    image_url: '/images/products/product_46.jpg',
    brand: 'Joyory',
    reason: 'Lightweight, rapid-absorption barrier hydration without pore-clogging lipids.',
  },
  {
    product_id: 42,
    name: 'Joyory AHA 10% + BHA 2% Weekly Flash Facial',
    category: 'Exfoliant',
    category_slug: 'exfoliant',
    price: '999.00',
    image_url: '/images/products/product_42.jpg',
    brand: 'Joyory',
    reason: 'Dual-action chemical resurfacing treatment for radiant, glass-skin texture.',
  },
];

export default function Home({ user, onGoToShop, onSelectProduct, onAddToCart }) {

  // Wall items state initialized with randomly shuffled Joyory products (guarantees unique products per column)
  const [wallItems, setWallItems] = useState(() => {
    const initial = ALL_PRODUCTS.map((p) => ({
      id: p.id,
      productId: p.id,
      image: p.image_url || `/images/products/product_${p.id}.jpg`,
      title: p.name,
      price: formatRupees(p.price),
      category: p.category,
    }));
    return shuffleArray(initial);
  });

  useEffect(() => {
    fetchProducts()
      .then((data) => {
        const list = Array.isArray(data) ? data : (data?.results || []);
        if (list.length > 0) {
          const formatted = list.map((p) => ({
            id: p.id,
            productId: p.id,
            image: p.image_url || `/images/products/product_${p.id}.jpg`,
            title: p.name,
            price: formatRupees(p.price),
            category: p.category,
          }));
          setWallItems(shuffleArray(formatted));
        }
      })
      .catch((err) => {
        console.warn('Could not fetch products for DriftWall, using local catalog:', err);
      });
  }, []);


  const getSkinStorageKey = (u) => (u ? `joyory_skin_analysis_${u.id || u.username}` : 'joyory_skin_analysis_guest');

  const [skinResult, setSkinResult] = useState(() => {
    try {
      const key = getSkinStorageKey(user);
      const saved = localStorage.getItem(key);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [showRecommendations, setShowRecommendations] = useState(() => {
    try {
      const key = getSkinStorageKey(user);
      const saved = localStorage.getItem(key);
      return !!saved;
    } catch {
      return false;
    }
  });
  const recommendationsRef = useRef(null);

  // Reload skin analysis state whenever user changes (login, logout, switch)
  useEffect(() => {
    try {
      const key = getSkinStorageKey(user);
      const saved = localStorage.getItem(key);
      const parsed = saved ? JSON.parse(saved) : null;
      setSkinResult(parsed);
      setShowRecommendations(!!parsed);
    } catch {
      setSkinResult(null);
      setShowRecommendations(false);
    }
  }, [user]);

  const handleViewRecommendations = (result) => {
    const dataToUse = result || skinResult;
    if (dataToUse) {
      setSkinResult(dataToUse);
    }
    setShowRecommendations(true);

    const scrollToTarget = () => {
      const anchor = document.getElementById('recommendations-anchor') || recommendationsRef.current;
      if (anchor) {
        anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } else {
        const driftWall = document.querySelector('.drift-wall-wrapper');
        if (driftWall) {
          const top = driftWall.getBoundingClientRect().top + window.pageYOffset + driftWall.offsetHeight - 40;
          window.scrollTo({ top, behavior: 'smooth' });
        }
      }
    };

    scrollToTarget();
    setTimeout(scrollToTarget, 60);
    setTimeout(scrollToTarget, 250);
  };

  return (
    <div className="home-container">
      {/* Editorial Luxury Hero with Reactive GridPulse Background */}
      <section className="hero-section">
          <GridPulse cell={24} reach={2.8} ambient={2} avoid="[data-grid-avoid]" />
          <div className="hero-content">
            <div className="hero-tag" data-grid-avoid>
              <SparklesIcon size={14} />
              <span>Hackathon Task 02 &bull; Smart Shopping Experience</span>
            </div>
            <h1 className="hero-headline" data-grid-avoid>
              Intelligent Skincare.<br />
              Harmonized Routines.
            </h1>
            <p className="hero-lead" data-grid-avoid>
              Meet Joyory — the first beauty platform engineered with active ingredient conflict detection, hyper-local climate adaptation, and progressive habit-building routines.
            </p>
            <div className="hero-actions" data-grid-avoid>
              <button className="btn-hero-primary" onClick={onGoToShop}>
                <span>Explore Smart Catalog</span>
                <ArrowRightIcon size={18} />
              </button>
            </div>
          </div>

          <div className="hero-visual" data-grid-avoid style={{ position: 'relative', left: '20px' }}>
            <ReflectiveCard
              user={user}
              overlayColor="rgba(0, 0, 0, 0.2)"
              blurStrength={12}
              glassDistortion={30}
              metalness={1}
              roughness={0.75}
              displacementStrength={20}
              noiseScale={1}
              specularConstant={0}
              grayscale={0.15}
              color="#ffffff"
              onAddToCart={onAddToCart}
              onAnalysisComplete={setSkinResult}
              onResetAnalysis={() => {
                setSkinResult(null);
                setShowRecommendations(false);
              }}
              onViewRecommendations={handleViewRecommendations}
            />
          </div>
        </section>

      {/* DriftWall 3D Floating Effect Area with Real Product Photos */}
      <div
        className="drift-wall-wrapper"
        style={{
          height: 600,
          width: '100%',
          position: 'relative',
          overflow: 'hidden',
          borderRadius: '24px',
          background: 'var(--bg-main, #fcfbf9)',
        }}
      >

        <DriftWall
          items={wallItems}
          columns={5}
          tileWidth={236}
          tileHeight={192}
          gap={18}
          tilt={19}
          turn={-16}
          perspective={1800}
          depth={70}
          speed={36}
          direction="up"
          variance={0.5}
          parallax={0.9}
          lift={44}
          fade={0.65}
          dim={1}
          overlayColor="#ffffff"
          radius={33}
          roll={7}
          pauseOnHover={false}
          grayscale={false}
          onItemClick={(item) => {
            if (item.productId && onSelectProduct) {
              onSelectProduct(item.productId);
            }
          }}
        />
      </div>

      {/* Scroll Anchor directly below hero */}
      <div
        id="recommendations-anchor"
        ref={recommendationsRef}
        style={{ scrollMarginTop: '100px', height: '1px', width: '100%' }}
      />

      {/* Below Second Photo Part: Product Recommendations Section */}
      {(showRecommendations || (skinResult?.recommendations && skinResult.recommendations.length > 0)) && (
        <section
          id="skin-recommendations-section"
          className="skin-recommendations-section"
        >
          <div className="reco-section-header">
            <div className="reco-section-tag">
              <SparklesIcon size={14} />
              <span>Personalized Clinical Prescription</span>
            </div>
            <h2 className="reco-section-title">
              Targeted Formulations For Your Skin Profile
            </h2>
            <p className="reco-section-subtitle">
              {skinResult?.analysis?.skin_type
                ? `Based on your skin analysis (${skinResult.analysis.skin_type} skin • Skin Health ${Math.round(skinResult.analysis.overall_health_score || 0)}/100), our engine matched these specific Joyory products to balance your active biomarkers without ingredient conflicts.`
                : 'Based on dermatological skin profiling, our engine matched these specific Joyory active formulas to optimize your skin barrier and enhance radiance.'}
            </p>

            {skinResult?.analysis && (
              <div className="reco-profile-badges">
                {skinResult.analysis?.skin_type && (
                  <span className="profile-pill">
                    Skin Type: <strong>{skinResult.analysis.skin_type}</strong>
                  </span>
                )}
                {Object.entries(skinResult.analysis?.metrics || {}).map(([k, v]) => {
                  const lvl = typeof v === 'object' ? (v.level || v.value) : v;
                  if (!lvl || lvl.toString().toLowerCase() === 'low') return null;
                  return (
                    <span key={k} className="profile-pill pill-highlight">
                      {k.replace(/_/g, ' ')}: <strong>{lvl}</strong>
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          <div className="reco-products-grid">
            {((skinResult?.recommendations && skinResult.recommendations.length > 0)
              ? skinResult.recommendations
              : DEFAULT_RECOMMENDATIONS
            ).map((rec) => (
              <RecommendedProductCard
                key={rec.product_id}
                rec={rec}
                onSelectProduct={onSelectProduct}
                onAddToCart={onAddToCart}
              />
            ))}
          </div>

          <div className="reco-section-footer">
            <button className="btn-hero-primary" onClick={onGoToShop}>
              <span>Explore Complete Smart Catalog</span>
              <ArrowRightIcon size={18} />
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

