from django.core.management.base import BaseCommand
from products.models import Ingredient, IngredientInteraction, Product

class Command(BaseCommand):
    help = "Seeds 65+ realistic demo skincare products, ingredients, and interaction rules for Joyory."

    def handle(self, *args, **options):
        self.stdout.write("Seeding ingredients...")
        ingredients_data = [
            # Retinoids
            ("Retinol", "retinoid", "Vitamin A derivative that accelerates cellular turnover and collagen synthesis."),
            ("Granactive Retinoid", "retinoid", "Next-generation hydroxypinacolone retinoate providing retinoid benefits with low irritation."),
            ("Bakuchiol", "retinoid", "Plant-derived natural retinol alternative suitable for sensitive skin."),

            # Exfoliants (AHAs & BHAs & PHAs)
            ("Glycolic Acid (AHA)", "exfoliant", "Smallest alpha hydroxy acid molecule that chemically exfoliates dead skin surface cells."),
            ("Lactic Acid (AHA)", "exfoliant", "Gentler hydrating AHA that smooths texture and improves moisture retention."),
            ("Mandelic Acid (AHA)", "exfoliant", "Larger molecular weight AHA offering exceptionally gentle surface renewal."),
            ("Salicylic Acid (BHA)", "exfoliant", "Oil-soluble beta hydroxy acid that dissolves sebum and clears pore blockages."),
            ("Gluconolactone (PHA)", "exfoliant", "Polyhydroxy acid providing ultra-mild exfoliation with humectant benefits."),

            # Antioxidants & Brighteners
            ("L-Ascorbic Acid (Vitamin C)", "antioxidant", "Pure, potent antioxidant that neutralizes free radicals and brightens hyperpigmentation."),
            ("Ethyl Ascorbic Acid", "antioxidant", "Highly stable Vitamin C ether that illuminates and boosts firmness."),
            ("Niacinamide (Vitamin B3)", "antioxidant", "Multifunctional ingredient that regulates sebum, minimizes pores, and supports barrier lipids."),
            ("Azelaic Acid", "antioxidant", "Dicarboxylic acid that reduces redness, calms blemish swelling, and evens skin tone."),
            ("Tranexamic Acid", "antioxidant", "Amino acid derivative that visibly fades stubborn UV-induced discoloration."),
            ("Alpha Arbutin", "antioxidant", "Safe botanical skin brightener that diminishes dark spots and post-acne marks."),
            ("Green Tea EGCG Extract", "antioxidant", "Polyphenol powerhouse that soothes inflammation and shields against oxidative stress."),

            # Humectants & Hydrators
            ("Hyaluronic Acid", "humectant", "Deeply hydrating humectant capable of holding up to 1000x its weight in water."),
            ("Polyglutamic Acid", "humectant", "High molecular weight humectant holding up to 5x more moisture than hyaluronic acid."),
            ("Glycerin", "humectant", "Classic natural humectant that restores skin suppleness and maintains hydration balance."),
            ("Panthenol (Vitamin B5)", "humectant", "Pro-vitamin that accelerates barrier healing, relieves dryness, and reduces redness."),

            # Lipids & Barrier Support
            ("Ceramide NP", "lipid", "Bio-identical epidermal lipid that locks in moisture and fortifies skin barrier integrity."),
            ("Squalane", "lipid", "Non-comedogenic weightless olive-derived lipid that restores skin lipid softness."),
            ("Cholesterol", "lipid", "Essential component of natural lipid bilayers that optimizes barrier repair with ceramides."),
            ("Colloidal Oatmeal", "soothing", "Clinically proven barrier-calming prebiotic emollient relieving itchiness and irritation."),

            # Soothing & Botanicals
            ("Centella Asiatica", "soothing", "Traditional calming botanical extract rich in madecassoside that quells reactive redness."),
            ("Madecassoside", "soothing", "Isolated bioactive compound of Centella Asiatica that accelerates tissue repair."),
            ("Allantoin", "soothing", "Gentle keratolytic agent that moisturizes and comforts sensitized skin."),
            ("Mugwort Extract", "soothing", "Calming Korean herbal botanical that detoxifies and relieves inflamed skin."),

            # Sunscreen Filters
            ("Zinc Oxide", "sunscreen_filter", "Mineral physical UV filter providing broad-spectrum UVA and UVB defense."),
            ("Titanium Dioxide", "sunscreen_filter", "Mineral physical UV filter reflecting both UVA and UVB rays."),

            # Peptides
            ("Copper Tripeptide-1", "peptide", "Signaling peptide complex supporting collagen remodeling and skin firmness."),
            ("Matrixyl 3000", "peptide", "Dual peptide blend stimulating extracellular matrix renewal and fine line reduction."),
            ("Argireline (Acetyl Hexapeptide-8)", "peptide", "Targeted peptide that relaxes the appearance of facial dynamic expression lines."),
        ]

        ing_objs = {}
        for name, cat, desc in ingredients_data:
            obj, _ = Ingredient.objects.update_or_create(
                name=name,
                defaults={"category": cat, "description": desc}
            )
            ing_objs[name] = obj

        self.stdout.write("Seeding ingredient interaction rules...")
        interactions = [
            # Retinol + Exfoliants (High Warnings)
            (
                ing_objs["Retinol"],
                ing_objs["Glycolic Acid (AHA)"],
                "warning",
                "irritation_risk",
                "Using Retinol and Alpha Hydroxy Acids simultaneously may compromise barrier function and trigger irritation or peeling.",
                "Consider separating their use: use AHA 1–2 times weekly and Retinol on alternate evenings."
            ),
            (
                ing_objs["Retinol"],
                ing_objs["Salicylic Acid (BHA)"],
                "warning",
                "barrier_stress",
                "Combining Retinol with BHA increases dryness and barrier stress, especially on sensitive skin types.",
                "Alternate application nights or reserve BHA for targeted morning cleansing and Retinol for nighttime."
            ),
            (
                ing_objs["Retinol"],
                ing_objs["Lactic Acid (AHA)"],
                "warning",
                "irritation_risk",
                "Simultaneous application of Retinol and Lactic Acid can overwhelm the epidermal barrier.",
                "Separate their use: Lactic Acid in the evening on days when not using Retinol."
            ),
            # Chemical Exfoliant Layering (Cautions)
            (
                ing_objs["Glycolic Acid (AHA)"],
                ing_objs["Salicylic Acid (BHA)"],
                "caution",
                "irritation_risk",
                "Layering multiple leave-on chemical exfoliants at once can cause over-exfoliation and redness.",
                "Alternate usage days or select a single formula calibrated for your predominant skin concern."
            ),
            (
                ing_objs["Lactic Acid (AHA)"],
                ing_objs["Salicylic Acid (BHA)"],
                "caution",
                "irritation_risk",
                "Using both AHA and BHA concurrently may thin the stratum corneum if not spaced.",
                "Alternate between days or use a balanced formula containing lower concentrations of each."
            ),
            # Vitamin C + Acids (pH sensitivity)
            (
                ing_objs["L-Ascorbic Acid (Vitamin C)"],
                ing_objs["Glycolic Acid (AHA)"],
                "caution",
                "ph_dependency",
                "Both are low-pH formulas. Layering them together in one session can cause temporary stinging or flushing.",
                "Use Vitamin C during your morning routine for antioxidant defense, and AHA in your evening routine."
            ),
            (
                ing_objs["L-Ascorbic Acid (Vitamin C)"],
                ing_objs["Salicylic Acid (BHA)"],
                "caution",
                "ph_dependency",
                "Simultaneous low pH application may cause mild facial flushing.",
                "Apply Vitamin C in the morning and BHA in the evening."
            ),
            # Retinol + Peptides
            (
                ing_objs["Retinol"],
                ing_objs["Copper Tripeptide-1"],
                "caution",
                "reduced_efficacy",
                "Direct simultaneous layering of high-strength retinoids with copper peptides may reduce peptide stability.",
                "Use copper peptides in morning routines and Retinol at night."
            ),
            (
                ing_objs["L-Ascorbic Acid (Vitamin C)"],
                ing_objs["Copper Tripeptide-1"],
                "caution",
                "reduced_efficacy",
                "Copper ions can oxidize pure L-Ascorbic Acid, diminishing antioxidant efficacy.",
                "Separate their use: Vitamin C in AM, Copper Peptides in PM."
            ),
            # Safe & Synergistic Pairs (Info)
            (
                ing_objs["L-Ascorbic Acid (Vitamin C)"],
                ing_objs["Niacinamide (Vitamin B3)"],
                "info",
                "compatible_synergy",
                "Modern stabilized formulations of Vitamin C and Niacinamide work synergistically for tone clarity and radiance.",
                "Apply the lighter texture first or allow 1–2 minutes to absorb."
            ),
            (
                ing_objs["Retinol"],
                ing_objs["Hyaluronic Acid"],
                "info",
                "compatible_synergy",
                "Hyaluronic Acid acts as a soothing hydration cushion, counteracting potential dryness from retinoids.",
                "Safe and recommended to use together; apply hyaluronic acid before or mixed with your moisturizer."
            ),
            (
                ing_objs["Ceramide NP"],
                ing_objs["Retinol"],
                "info",
                "compatible_synergy",
                "Ceramides fortify the lipid matrix, making retinoid introduction significantly gentler and more tolerable.",
                "Recommended to follow active treatments with ceramide-rich moisturizers."
            ),
            (
                ing_objs["Niacinamide (Vitamin B3)"],
                ing_objs["Salicylic Acid (BHA)"],
                "info",
                "compatible_synergy",
                "Niacinamide regulates sebum while BHA exfoliates inside pores, delivering complementary pore-refining benefits.",
                "Safe to use in the same routine."
            ),
            (
                ing_objs["Azelaic Acid"],
                ing_objs["Niacinamide (Vitamin B3)"],
                "info",
                "compatible_synergy",
                "Outstanding synergistic combination for redness calming, tone refinement, and skin soothing.",
                "Safe and gentle for daily combination."
            ),
            (
                ing_objs["Centella Asiatica"],
                ing_objs["Retinol"],
                "info",
                "compatible_synergy",
                "Centella Asiatica dampens cellular inflammation and buffers the skin when using active retinoids.",
                "Excellent combination for maintaining a calm skin barrier."
            ),
            (
                ing_objs["Hyaluronic Acid"],
                ing_objs["Polyglutamic Acid"],
                "info",
                "compatible_synergy",
                "Multi-depth hydration synergy: Polyglutamic seals the surface while Hyaluronic hydrates deeper strata.",
                "Layer freely for intense skin plumping."
            ),
            (
                ing_objs["Ceramide NP"],
                ing_objs["Squalane"],
                "info",
                "compatible_synergy",
                "Complete lipid barrier replication mimicking natural sebum.",
                "Ideal for dry or damaged skin recovery."
            ),
        ]

        for a, b, sev, itype, msg, rec in interactions:
            IngredientInteraction.objects.update_or_create(
                ingredient_a=a,
                ingredient_b=b,
                defaults={
                    "severity": sev,
                    "interaction_type": itype,
                    "message": msg,
                    "recommendation": rec
                }
            )

        self.stdout.write("Seeding 65+ realistic Joyory products...")
        products_data = [
            # ----------------------------------------------------
            # 1. CLEANSERS (10 Products)
            # ----------------------------------------------------
            {
                "name": "Joyory Barrier Calm Gentle Cleanser",
                "category": "cleanser",
                "price": 18.00,
                "description": "A comforting cream-to-foam cleanser with ceramides and centella that purifies without stripping.",
                "texture": "foam",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Ceramide NP", "Centella Asiatica", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Hydro-Infusion Gel Cleanser",
                "category": "cleanser",
                "price": 19.50,
                "description": "A refreshing electrolyte water cleanser that drenches the skin in moisture while removing pollutants.",
                "texture": "gel",
                "suitable_climate": "hot_dry",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Hyaluronic Acid", "Centella Asiatica"]
            },
            {
                "name": "Joyory Pore Clarifying BHA Foaming Wash",
                "category": "cleanser",
                "price": 21.00,
                "description": "Deep pore foaming wash with 1% salicylic acid to gently clear congestions and control oil.",
                "texture": "foam",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 60,
                "ingredients": ["Salicylic Acid (BHA)", "Green Tea EGCG Extract"]
            },
            {
                "name": "Joyory Nourishing Squalane Melt Cleansing Oil",
                "category": "cleanser",
                "price": 24.00,
                "description": "Silky botanical first-step oil cleanser that melts waterproof SPF and urban grime without greasy residue.",
                "texture": "oil",
                "suitable_climate": "all",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 75,
                "ingredients": ["Squalane", "Centella Asiatica"]
            },
            {
                "name": "Joyory Colloidal Oat Soothing Cleansing Balm",
                "category": "cleanser",
                "price": 23.50,
                "description": "Rich melting balm formulated with micro-milled colloidal oatmeal to comfort sensitized skin.",
                "texture": "rich_cream",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 60,
                "ingredients": ["Colloidal Oatmeal", "Ceramide NP"]
            },
            {
                "name": "Joyory PHA Micro-Polish Daily Jelly Wash",
                "category": "cleanser",
                "price": 22.00,
                "description": "Bouncy jelly cleanser infused with gentle gluconolactone PHA for smooth, reflective skin texture.",
                "texture": "gel",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 60,
                "ingredients": ["Gluconolactone (PHA)", "Glycerin"]
            },
            {
                "name": "Joyory Mugwort Calming Bubble Cleanser",
                "category": "cleanser",
                "price": 20.00,
                "description": "Self-foaming botanical cloud cleanser that relieves heated, stressed, or acne-prone skin.",
                "texture": "foam",
                "suitable_climate": "hot_humid",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 55,
                "ingredients": ["Mugwort Extract", "Allantoin"]
            },
            {
                "name": "Joyory Prebiotic Milky Comfort Wash",
                "category": "cleanser",
                "price": 22.50,
                "description": "Velvety non-foaming milk wash that replenishes skin microflora and preserves delicate pH levels.",
                "texture": "lightweight_lotion",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Ceramide NP", "Panthenol (Vitamin B5)"]
            },
            {
                "name": "Joyory Micellar Cleansing Hydration Essence",
                "category": "cleanser",
                "price": 17.00,
                "description": "Rinse-free botanical micellar water that captures fine dust and makeup with zero tugging.",
                "texture": "liquid",
                "suitable_climate": "all",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 70,
                "ingredients": ["Hyaluronic Acid", "Centella Asiatica"]
            },
            {
                "name": "Joyory Salicylic + Green Tea Purifying Bar",
                "category": "cleanser",
                "price": 14.50,
                "description": "Solid pH-balanced syndet cleanser bar targeting body and facial breakouts with pore-refining BHA.",
                "texture": "foam",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 80,
                "ingredients": ["Salicylic Acid (BHA)", "Green Tea EGCG Extract"]
            },

            # ----------------------------------------------------
            # 2. TONERS (8 Products)
            # ----------------------------------------------------
            {
                "name": "Joyory Calming Centella Balancing Toner",
                "category": "toner",
                "price": 22.00,
                "description": "Gentle alcohol-free botanical toner that balances skin pH and soothes redness after cleansing.",
                "texture": "liquid",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 70,
                "ingredients": ["Centella Asiatica", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Multi-Molecular Hyaluronic Acid Mist",
                "category": "toner",
                "price": 21.00,
                "description": "Micro-diffused face mist delivering 4 molecular weights of hyaluronic acid for instant bounce.",
                "texture": "liquid",
                "suitable_climate": "hot_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Hyaluronic Acid", "Polyglutamic Acid"]
            },
            {
                "name": "Joyory Ceramide Barrier Relief Milky Toner",
                "category": "toner",
                "price": 25.00,
                "description": "Emulsion-rich liquid skin softener infused with ceramides and cholesterol to repair compromised skin.",
                "texture": "liquid",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 65,
                "ingredients": ["Ceramide NP", "Cholesterol", "Panthenol (Vitamin B5)"]
            },
            {
                "name": "Joyory Mandelic Acid 5% Gentle Prep Tonic",
                "category": "toner",
                "price": 24.50,
                "description": "Super-gentle daily exfoliating toner suitable for melanin-rich and sensitive skin types.",
                "texture": "liquid",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 75,
                "ingredients": ["Mandelic Acid (AHA)", "Centella Asiatica"]
            },
            {
                "name": "Joyory Mugwort Essence 100% First Treatment",
                "category": "toner",
                "price": 27.00,
                "description": "Fermented single-origin mugwort liquid essence that visibly reduces flushing and calms breakout stress.",
                "texture": "liquid",
                "suitable_climate": "hot_humid",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Mugwort Extract", "Allantoin"]
            },
            {
                "name": "Joyory Green Tea Sebum Control Toner",
                "category": "toner",
                "price": 20.00,
                "description": "Astringent-free balancing toner with Jeju green tea that normalizes midday T-zone oiliness.",
                "texture": "liquid",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 70,
                "ingredients": ["Green Tea EGCG Extract", "Niacinamide (Vitamin B3)"]
            },
            {
                "name": "Joyory Panthenol 5% Deep Hydrating Tonic",
                "category": "toner",
                "price": 23.00,
                "description": "Viscous hydrating toner infused with concentrated Vitamin B5 to comfort tight, thirsty skin.",
                "texture": "liquid",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Panthenol (Vitamin B5)", "Glycerin"]
            },
            {
                "name": "Joyory PHA 3% Moisture Prep Liquid",
                "category": "toner",
                "price": 23.50,
                "description": "Non-stinging polyhydroxy acid toner that gently sweeps debris while drenching surface cells in moisture.",
                "texture": "liquid",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 65,
                "ingredients": ["Gluconolactone (PHA)", "Hyaluronic Acid"]
            },

            # ----------------------------------------------------
            # 3. SERUMS (15 Products)
            # ----------------------------------------------------
            {
                "name": "Joyory Glow Vitality 15% Vitamin C Serum",
                "category": "serum",
                "price": 34.00,
                "description": "High-potency stabilized pure Vitamin C antioxidant serum protecting against free radicals and environmental stress.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 50,
                "ingredients": ["L-Ascorbic Acid (Vitamin C)", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Clarifying Balance 10% Niacinamide Serum",
                "category": "serum",
                "price": 28.00,
                "description": "Concentrated Niacinamide serum that refines enlarged pores, regulates oil, and soothes stressed skin.",
                "texture": "lightweight_lotion",
                "suitable_climate": "hot_humid",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Niacinamide (Vitamin B3)", "Centella Asiatica"]
            },
            {
                "name": "Joyory Midnight Renewal 0.5% Retinol Treatment",
                "category": "serum",
                "price": 38.00,
                "description": "Micro-encapsulated slow-release retinol designed to promote cell renewal and smooth fine texture with minimal irritation.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "high",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 75,
                "ingredients": ["Retinol", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Gentle Hydrating Recovery Serum",
                "category": "serum",
                "price": 31.00,
                "description": "Safe, non-irritating hydration serum with ceramides and hyaluronic acid that can be paired with any active.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Hyaluronic Acid", "Ceramide NP"]
            },
            {
                "name": "Joyory Granactive Retinoid 2% Emulsion",
                "category": "serum",
                "price": 36.00,
                "description": "Gentle direct-binding retinoid emulsion delivering potent resurfacing results without the redness or flaking of classic retinol.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 60,
                "ingredients": ["Granactive Retinoid", "Squalane"]
            },
            {
                "name": "Joyory Bakuchiol 1% Botanical Alternative Serum",
                "category": "serum",
                "price": 33.00,
                "description": "Photostable plant-derived alternative to retinol that smooths fine lines and supports firmness safely day or night.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Bakuchiol", "Centella Asiatica"]
            },
            {
                "name": "Joyory Copper Tripeptide-1 Firming Booster",
                "category": "serum",
                "price": 42.00,
                "description": "Vibrant blue signaling peptide concentrate that supports skin density, collagen synthesis, and barrier elasticity.",
                "texture": "gel",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "high",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 50,
                "ingredients": ["Copper Tripeptide-1", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Matrixyl 3000 + Argireline Peptide Complex",
                "category": "serum",
                "price": 35.00,
                "description": "Dual peptide synergy targeting expression lines and boosting skin cushion for a plump, lifted appearance.",
                "texture": "gel",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Matrixyl 3000", "Argireline (Acetyl Hexapeptide-8)"]
            },
            {
                "name": "Joyory Azelaic Acid 10% Calming Suspension",
                "category": "serum",
                "price": 29.00,
                "description": "Multi-action gel-cream suspension that visibly calms persistent redness, fades dark spots, and refines bumpy texture.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Azelaic Acid", "Centella Asiatica"]
            },
            {
                "name": "Joyory Tranexamic Acid 5% Dark Spot Eraser",
                "category": "serum",
                "price": 36.50,
                "description": "Advanced hyperpigmentation formula targeting post-sun marks, melasma shadows, and stubborn uneven tone.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Tranexamic Acid", "Niacinamide (Vitamin B3)"]
            },
            {
                "name": "Joyory Alpha Arbutin 2% Radiance Drops",
                "category": "serum",
                "price": 27.00,
                "description": "High-purity botanical arbutin combined with hyaluronic acid for targeted fading of hyperpigmentation.",
                "texture": "liquid",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Alpha Arbutin", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Polyglutamic Moisture Lock Elixir",
                "category": "serum",
                "price": 32.00,
                "description": "Ultra-quenching humectant serum that forms a breathable moisture veil to eliminate dehydration fine lines.",
                "texture": "gel",
                "suitable_climate": "hot_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Polyglutamic Acid", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Centella Madecassoside Rescue Ampoule",
                "category": "serum",
                "price": 30.00,
                "description": "Concentrated emergency soothing ampoule that instantly calms over-exfoliated or post-sun sensitized skin.",
                "texture": "gel",
                "suitable_climate": "all",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 50,
                "ingredients": ["Madecassoside", "Centella Asiatica", "Panthenol (Vitamin B5)"]
            },
            {
                "name": "Joyory 100% Plant-Derived Squalane Glow Drops",
                "category": "serum",
                "price": 22.00,
                "description": "Pure weightless lipid oil that seals in moisture and instantly restores dewy luminosity without pore clogging.",
                "texture": "oil",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 90,
                "ingredients": ["Squalane"]
            },
            {
                "name": "Joyory Ethyl Ascorbic 10% Daily Brightening Fluid",
                "category": "serum",
                "price": 33.00,
                "description": "Ultra-stable non-oxidizing Vitamin C derivative fluid suitable for skin that experiences stinging from L-ascorbic acid.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 55,
                "ingredients": ["Ethyl Ascorbic Acid", "Glycerin"]
            },

            # ----------------------------------------------------
            # 4. EXFOLIANTS (7 Products)
            # ----------------------------------------------------
            {
                "name": "Joyory Resurfacing 7% Glycolic AHA Exfoliator",
                "category": "exfoliant",
                "price": 26.00,
                "description": "Chemical exfoliant tonic that sweeps away dull dead skin cells to reveal smoother, brighter skin.",
                "texture": "liquid",
                "suitable_climate": "all",
                "hydration_level": "light",
                "active_level": "high",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 90,
                "ingredients": ["Glycolic Acid (AHA)"]
            },
            {
                "name": "Joyory Pore Refining 2% BHA Clearing Liquid",
                "category": "exfoliant",
                "price": 27.50,
                "description": "Salicylic acid exfoliant that dissolves pore debris, balances excess shine, and reduces congestion.",
                "texture": "liquid",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "high",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 90,
                "ingredients": ["Salicylic Acid (BHA)", "Centella Asiatica"]
            },
            {
                "name": "Joyory Lactic Acid 10% + HA Gentle Peeling Serum",
                "category": "exfoliant",
                "price": 25.00,
                "description": "Mild lactic acid superficial peeling formulation combined with tasmanian pepperberry to mitigate signs of sensitivity.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "high",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 75,
                "ingredients": ["Lactic Acid (AHA)", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory PHA 10% Water Resurfacing Glow Solution",
                "category": "exfoliant",
                "price": 29.00,
                "description": "Gentle chemical exfoliator using large-molecule polyhydroxy acids to hydrate and smooth with zero downtime.",
                "texture": "liquid",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 80,
                "ingredients": ["Gluconolactone (PHA)", "Centella Asiatica"]
            },
            {
                "name": "Joyory Mandelic 10% + Centella Resurfacing Serum",
                "category": "exfoliant",
                "price": 28.00,
                "description": "Gentle slow-penetrating AHA serum specifically calibrated for sensitive and hyperpigmentation-prone skin.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 75,
                "ingredients": ["Mandelic Acid (AHA)", "Centella Asiatica"]
            },
            {
                "name": "Joyory AHA 10% + BHA 2% Weekly Flash Facial",
                "category": "exfoliant",
                "price": 32.00,
                "description": "Intensive rinse-off exfoliating mask treatment targeting stubborn textural roughness and congested pores.",
                "texture": "gel",
                "suitable_climate": "all",
                "hydration_level": "light",
                "active_level": "high",
                "usage_frequency": "weekly",
                "time_of_day": "evening",
                "typical_duration_days": 120,
                "ingredients": ["Glycolic Acid (AHA)", "Salicylic Acid (BHA)"]
            },
            {
                "name": "Joyory Gentle Rice Enzyme Polishing Powder",
                "category": "exfoliant",
                "price": 26.50,
                "description": "Water-activated botanical micro-exfoliant powder that gently buffs away dull flakes with zero scratching.",
                "texture": "foam",
                "suitable_climate": "all",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 90,
                "ingredients": ["Allantoin", "Colloidal Oatmeal"]
            },

            # ----------------------------------------------------
            # 5. MOISTURIZERS (10 Products)
            # ----------------------------------------------------
            {
                "name": "Joyory Deep Barrier Restoring Cream",
                "category": "moisturizer",
                "price": 32.00,
                "description": "Rich nourishing lipid barrier cream formulated with bio-identical ceramides and cica to repair stressed skin.",
                "texture": "rich_cream",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Ceramide NP", "Centella Asiatica"]
            },
            {
                "name": "Joyory Hydro-Burst Cloud Water Gel",
                "category": "moisturizer",
                "price": 30.00,
                "description": "Ultra-lightweight oil-free water gel that bursts into cooling hydration without clogging pores in humid climates.",
                "texture": "gel",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Hyaluronic Acid", "Centella Asiatica"]
            },
            {
                "name": "Joyory Squalane + Ceramide Balanced Fluid",
                "category": "moisturizer",
                "price": 31.00,
                "description": "Silky feather-light daily moisturizing fluid that delivers deep lipid replenishment with zero grease.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Squalane", "Ceramide NP", "Cholesterol"]
            },
            {
                "name": "Joyory Cica Repair Recovery Balm",
                "category": "moisturizer",
                "price": 28.00,
                "description": "Dense occlusive recovery balm targeting dry patches, wind burn, and localized micro-fissures.",
                "texture": "rich_cream",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 75,
                "ingredients": ["Madecassoside", "Panthenol (Vitamin B5)"]
            },
            {
                "name": "Joyory Niacinamide Oil-Free Mattifying Gel",
                "category": "moisturizer",
                "price": 29.50,
                "description": "Cooling electrolyte gel moisturizer with 4% niacinamide to eliminate midday glare and blur visible pores.",
                "texture": "gel",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Niacinamide (Vitamin B3)", "Green Tea EGCG Extract"]
            },
            {
                "name": "Joyory Peptide Firming Day Moisturizer",
                "category": "moisturizer",
                "price": 38.00,
                "description": "Velvety multi-peptide cream designed to support facial contour resilience and lock in morning hydration.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 55,
                "ingredients": ["Matrixyl 3000", "Ceramide NP"]
            },
            {
                "name": "Joyory Colloidal Oatmeal Barrier Shield Lotion",
                "category": "moisturizer",
                "price": 26.00,
                "description": "Dermatologist-tested soothing lotion formulated to calm reactive and eczema-prone dry skin.",
                "texture": "lightweight_lotion",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 65,
                "ingredients": ["Colloidal Oatmeal", "Allantoin"]
            },
            {
                "name": "Joyory Panthenol 10% Intensive Barrier Ointment",
                "category": "moisturizer",
                "price": 27.00,
                "description": "High-concentration provitamin B5 ointment that acts as an invisible shield over micro-sensitized skin.",
                "texture": "rich_cream",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 70,
                "ingredients": ["Panthenol (Vitamin B5)", "Glycerin"]
            },
            {
                "name": "Joyory Pure Hyaluronic Daily Dew Moisturizer",
                "category": "moisturizer",
                "price": 28.50,
                "description": "Refreshing gel-cream combining 3 weights of hyaluronic acid for a glazed, supple dewy finish.",
                "texture": "gel",
                "suitable_climate": "hot_dry",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Hyaluronic Acid", "Squalane"]
            },
            {
                "name": "Joyory Overnight Barrier Ceramide Mask",
                "category": "moisturizer",
                "price": 34.00,
                "description": "Sleep recovery mask that forms a lipid envelope over nighttime skincare, revealing restored bounce by morning.",
                "texture": "rich_cream",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 80,
                "ingredients": ["Ceramide NP", "Polyglutamic Acid"]
            },

            # ----------------------------------------------------
            # 6. SUNSCREENS (8 Products)
            # ----------------------------------------------------
            {
                "name": "Joyory Invisible Shield Mineral SPF 50+",
                "category": "sunscreen",
                "price": 29.00,
                "description": "Non-greasy sheer mineral sunscreen providing high broad-spectrum UV protection without white cast.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 45,
                "ingredients": ["Zinc Oxide", "Centella Asiatica"]
            },
            {
                "name": "Joyory Matte Velvet Mineral Sun Fluid SPF 50",
                "category": "sunscreen",
                "price": 31.00,
                "description": "Oil-absorbing mineral fluid with zinc oxide that blurs pores and leaves an undetectable satin finish.",
                "texture": "lightweight_lotion",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 45,
                "ingredients": ["Zinc Oxide", "Green Tea EGCG Extract"]
            },
            {
                "name": "Joyory Barrier Defense Tinted Mineral SPF 40",
                "category": "sunscreen",
                "price": 33.00,
                "description": "Universal sheer tinted mineral sunscreen that evens minor redness while neutralizing UVA, UVB, and blue light.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 50,
                "ingredients": ["Zinc Oxide", "Titanium Dioxide", "Niacinamide (Vitamin B3)"]
            },
            {
                "name": "Joyory Hydra-Infused Water Gel Sunscreen SPF 50+",
                "category": "sunscreen",
                "price": 30.00,
                "description": "Cooling chemical sun gel that melts like water into skin with zero stickiness or residue.",
                "texture": "gel",
                "suitable_climate": "hot_dry",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 45,
                "ingredients": ["Hyaluronic Acid", "Centella Asiatica"]
            },
            {
                "name": "Joyory Sensitive Skin Physical Shield SPF 30",
                "category": "sunscreen",
                "price": 27.00,
                "description": "Ultra-pure zinc oxide sun lotion developed specifically for highly reactive, rosacea-prone skin.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 50,
                "ingredients": ["Zinc Oxide", "Colloidal Oatmeal"]
            },
            {
                "name": "Joyory Glow Primer SPF 45 Broad Spectrum",
                "category": "sunscreen",
                "price": 32.00,
                "description": "Luminous hybrid sunscreen and makeup primer enriched with niacinamide for an instant radiant base.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 45,
                "ingredients": ["Zinc Oxide", "Niacinamide (Vitamin B3)"]
            },
            {
                "name": "Joyory Active Sport Water-Resistant SPF 50+",
                "category": "sunscreen",
                "price": 28.50,
                "description": "Sweat and water-resistant sport sunscreen designed for intense UV outdoor protection.",
                "texture": "lightweight_lotion",
                "suitable_climate": "hot_humid",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 40,
                "ingredients": ["Zinc Oxide", "Centella Asiatica"]
            },
            {
                "name": "Joyory Mineral Sun Stick Reapply Touch-Up SPF 50",
                "category": "sunscreen",
                "price": 24.00,
                "description": "Compact solid mineral sunscreen stick for hygienic touch-ups over makeup on ears, nose, and cheeks.",
                "texture": "oil",
                "suitable_climate": "all",
                "hydration_level": "light",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "morning",
                "typical_duration_days": 60,
                "ingredients": ["Zinc Oxide", "Squalane"]
            },

            # ----------------------------------------------------
            # 7. TREATMENTS (7 Products)
            # ----------------------------------------------------
            {
                "name": "Joyory Blemish Clarifying SOS Paste",
                "category": "treatment",
                "price": 21.00,
                "description": "Fast-acting targeted overnight spot treatment that calms surface redness and shrinks active blemishes.",
                "texture": "rich_cream",
                "suitable_climate": "all",
                "hydration_level": "light",
                "active_level": "high",
                "usage_frequency": "daily",
                "time_of_day": "evening",
                "typical_duration_days": 90,
                "ingredients": ["Salicylic Acid (BHA)", "Zinc Oxide", "Centella Asiatica"]
            },
            {
                "name": "Joyory Multi-Peptide Eye Awakening Cream",
                "category": "treatment",
                "price": 32.00,
                "description": "Lightweight contour cream formulated with Matrixyl and caffeine to smooth crow's feet and reduce puffiness.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 75,
                "ingredients": ["Matrixyl 3000", "Hyaluronic Acid"]
            },
            {
                "name": "Joyory Retinol 0.2% Gentle Eye Contour Balm",
                "category": "treatment",
                "price": 34.00,
                "description": "Low-dose encapsulated retinol balm designed specifically for delicate peri-orbital skin texture renewal.",
                "texture": "rich_cream",
                "suitable_climate": "all",
                "hydration_level": "deep",
                "active_level": "medium",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 90,
                "ingredients": ["Retinol", "Ceramide NP"]
            },
            {
                "name": "Joyory Lip Barrier Plump & Seal Treatment",
                "category": "treatment",
                "price": 16.00,
                "description": "Nourishing lip recovery balm with plant squalane and ceramides that eliminates flaking overnight.",
                "texture": "rich_cream",
                "suitable_climate": "cold_dry",
                "hydration_level": "deep",
                "active_level": "low",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Squalane", "Ceramide NP"]
            },
            {
                "name": "Joyory Post-Blemish Dark Spot Corrector",
                "category": "treatment",
                "price": 28.00,
                "description": "Focused spot applicator serum combining tranexamic acid and niacinamide for red and brown marks.",
                "texture": "gel",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "twice_daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Tranexamic Acid", "Niacinamide (Vitamin B3)"]
            },
            {
                "name": "Joyory Azelaic Redness Rescue Emulsion",
                "category": "treatment",
                "price": 31.00,
                "description": "Targeted redness-neutralizing treatment with azelaic acid and cica for flushing-prone cheeks.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "moderate",
                "active_level": "medium",
                "usage_frequency": "daily",
                "time_of_day": "both",
                "typical_duration_days": 60,
                "ingredients": ["Azelaic Acid", "Centella Asiatica"]
            },
            {
                "name": "Joyory Overnight Glycolic Glow Hand & Body Treatment",
                "category": "treatment",
                "price": 26.00,
                "description": "Smoothing AHA chemical exfoliant cream that eliminates keratosis pilaris and restores silky texture.",
                "texture": "lightweight_lotion",
                "suitable_climate": "all",
                "hydration_level": "deep",
                "active_level": "high",
                "usage_frequency": "2_3_times_per_week",
                "time_of_day": "evening",
                "typical_duration_days": 75,
                "ingredients": ["Glycolic Acid (AHA)", "Ceramide NP"]
            },
        ]

        PRICE_MAP = {
            14.5: 449.00, 16.0: 499.00, 17.0: 499.00, 18.0: 549.00, 19.5: 599.00,
            20.0: 599.00, 21.0: 649.00, 22.0: 649.00, 22.5: 699.00, 23.0: 699.00,
            23.5: 699.00, 24.0: 749.00, 24.5: 749.00, 25.0: 799.00, 26.0: 799.00,
            26.5: 799.00, 27.0: 849.00, 27.5: 849.00, 28.0: 899.00, 28.5: 899.00,
            29.0: 899.00, 29.5: 949.00, 30.0: 949.00, 31.0: 949.00, 32.0: 999.00,
            33.0: 1049.00, 34.0: 1099.00, 35.0: 1149.00, 36.0: 1199.00, 36.5: 1199.00,
            38.0: 1299.00, 42.0: 1499.00,
        }

        count = 0
        for p_data in products_data:
            ing_names = p_data.pop("ingredients")
            raw_price = p_data["price"]
            if raw_price in PRICE_MAP:
                p_data["price"] = PRICE_MAP[raw_price]
            # Set realistic luxury product image URL
            name_lower = p_data["name"].lower()
            if "vitamin c" in name_lower:
                p_data["image_url"] = "/images/products/vitamin_c.jpg"
            elif "retinol" in name_lower:
                p_data["image_url"] = "/images/products/retinol.jpg"
            else:
                p_data["image_url"] = f"/images/products/{p_data['category']}.jpg"

            prod, created = Product.objects.update_or_create(
                name=p_data["name"],
                defaults=p_data
            )
            prod.ingredients.set([ing_objs[n] for n in ing_names if n in ing_objs])
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} Joyory products into db.sqlite3!"))
