import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Img, continueRender, delayRender, staticFile} from 'remotion';

export const LARGEUR = 1240;
export const HAUTEUR = 1754;

const C = {
	encre: '#141012',
	vin: '#4a0f1f',
	bordeaux: '#7d1530',
	or: '#cfa548',
	orPale: '#e6cf98',
	creme: '#f4ece0',
};

const SERIF = "'Cormorant Garamond', serif";
const SANS = "'Montserrat', sans-serif";

// Bouteilles posées sur l'étagère, de gauche à droite (x = centre, h = hauteur affichée).
const BOUTEILLES = [
	{src: 'whisky_toki.png', ratio: 0.384, x: 178, h: 392},
	{src: 'blacailloux.png', ratio: 0.223, x: 322, h: 520},
	{src: 'gragnos_lou_daro.png', ratio: 0.258, x: 470, h: 548},
	{src: 'chateauneuf.png', ratio: 0.258, x: 620, h: 578},
	{src: 'balac.png', ratio: 0.242, x: 770, h: 548},
	{src: 'frezier.png', ratio: 0.266, x: 920, h: 534},
	{src: 'rhum_la_favorite.png', ratio: 0.317, x: 1064, h: 446},
];

// Terrines au premier plan.
const TERRINES = [
	{src: 'terrine_silure_gemini.png', ratio: 0.986, x: 516, h: 196},
	{src: 'terrine_poissons_loire_gemini.png', ratio: 0.988, x: 724, h: 196},
];

const ETAGERE_Y = 1040;
const PREMIER_PLAN_Y = 1186;

const SERVICES = [
	{icone: 'cadeau', titre: 'Coffrets', suite: '& idées cadeaux'},
	{icone: 'verres', titre: 'Soirées œnologiques', suite: '& découvertes'},
	{icone: 'bouteille', titre: 'Achat & conseil', suite: 'en magasin'},
	{icone: 'carte', titre: 'Conseil & élaboration', suite: 'de votre carte des vins'},
	{icone: 'alliances', titre: 'Célébrations, mariages', suite: '& événementiel'},
];

const Icone: React.FC<{nom: string}> = ({nom}) => {
	const trait = {fill: 'none', stroke: C.or, strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
	return (
		<svg width={34} height={34} viewBox="0 0 32 32">
			{nom === 'cadeau' && (
				<g {...trait}>
					<rect x={5} y={13} width={22} height={14} />
					<rect x={3.5} y={9} width={25} height={4} />
					<path d="M16 9v18M16 9c-2-5-8-5-7-1 1 2 5 1 7 1zM16 9c2-5 8-5 7-1-1 2-5 1-7 1z" />
				</g>
			)}
			{nom === 'verres' && (
				<g {...trait}>
					<path d="M6 4h8c0 6-1.5 9-4 9S6 10 6 4zM10 13v11M6.5 24h7" />
					<path d="M18 4h8c0 6-1.5 9-4 9s-4-3-4-9zM22 13v11M18.5 24h7" />
				</g>
			)}
			{nom === 'bouteille' && (
				<g {...trait}>
					<path d="M14 3h4v6c3 1.5 4 4 4 7v12a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1V16c0-3 1-5.5 4-7z" />
					<rect x={11.5} y={17} width={9} height={7} />
				</g>
			)}
			{nom === 'carte' && (
				<g {...trait}>
					<path d="M7 4h15l4 4v20H7z" />
					<path d="M11 11h11M11 15h11M11 19h8M11 23h6" />
				</g>
			)}
			{nom === 'alliances' && (
				<g {...trait}>
					<circle cx={12} cy={19} r={7} />
					<circle cx={20} cy={19} r={7} />
					<path d="M18 6l2-3 2 3-2 2z" />
				</g>
			)}
		</svg>
	);
};

const Polices: React.FC = () => {
	const [handle] = useState(() => delayRender('Chargement des polices'));
	useEffect(() => {
		const polices = [
			new FontFace('Cormorant Garamond', `url(${staticFile('fonts/CormorantGaramond.ttf')})`, {weight: '300 700'}),
			new FontFace('Cormorant Garamond', `url(${staticFile('fonts/CormorantGaramond-Italic.ttf')})`, {weight: '300 700', style: 'italic'}),
			new FontFace('Montserrat', `url(${staticFile('fonts/Montserrat.ttf')})`, {weight: '100 900'}),
		];
		Promise.all(polices.map((p) => p.load()))
			.then((chargees) => {
				chargees.forEach((p) => document.fonts.add(p));
				continueRender(handle);
			})
			.catch((e) => {
				console.error(e);
				continueRender(handle);
			});
	}, [handle]);
	return null;
};

const Produit: React.FC<{src: string; ratio: number; x: number; h: number; base: number; reflet: number}> = ({src, ratio, x, h, base, reflet}) => {
	const l = h * ratio;
	return (
		<>
			{/* ombre de contact */}
			<div
				style={{
					position: 'absolute',
					left: x - l * 0.62,
					top: base - 9,
					width: l * 1.24,
					height: 18,
					borderRadius: '50%',
					background: 'radial-gradient(closest-side, rgba(0,0,0,0.75), rgba(0,0,0,0))',
				}}
			/>
			{/* reflet sur l'étagère */}
			<Img
				src={staticFile(`produits/${src}`)}
				style={{
					position: 'absolute',
					left: x - l / 2,
					top: base,
					width: l,
					height: h,
					transform: 'scaleY(-1)',
					opacity: reflet,
					WebkitMaskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 22%)',
					maskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 22%)',
				}}
			/>
			<Img
				src={staticFile(`produits/${src}`)}
				style={{
					position: 'absolute',
					left: x - l / 2,
					top: base - h,
					width: l,
					height: h,
					filter: 'drop-shadow(0 10px 18px rgba(0,0,0,0.45))',
				}}
			/>
		</>
	);
};

const Libelle: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
	<div
		style={{
			fontFamily: SANS,
			fontWeight: 600,
			fontSize: 13,
			letterSpacing: 4.2,
			textTransform: 'uppercase',
			color: C.or,
			...style,
		}}
	>
		{children}
	</div>
);

export const Panneau: React.FC = () => {
	return (
		<AbsoluteFill style={{background: C.encre, color: C.creme, fontFamily: SANS, overflow: 'hidden', fontVariantNumeric: 'lining-nums'}}>
			<Polices />

			{/* Fond : halo lie-de-vin derrière les produits */}
			<AbsoluteFill
				style={{
					background: `radial-gradient(ellipse 760px 700px at 50% 47%, ${C.vin} 0%, rgba(74,15,31,0.55) 45%, rgba(20,16,18,0) 80%)`,
				}}
			/>
			<AbsoluteFill
				style={{
					background: 'radial-gradient(ellipse 420px 360px at 50% 52%, rgba(207,165,72,0.16), rgba(207,165,72,0) 75%)',
				}}
			/>

			{/* Grain léger */}
			<svg width={LARGEUR} height={HAUTEUR} style={{position: 'absolute', inset: 0, opacity: 0.07, mixBlendMode: 'overlay'}}>
				<filter id="grain">
					<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} stitchTiles="stitch" />
				</filter>
				<rect width="100%" height="100%" filter="url(#grain)" />
			</svg>

			{/* Double filet doré */}
			<div style={{position: 'absolute', inset: 26, border: `1.5px solid ${C.or}`, opacity: 0.85}} />
			<div style={{position: 'absolute', inset: 34, border: `0.75px solid ${C.or}`, opacity: 0.45}} />

			{/* En-tête */}
			<Libelle style={{position: 'absolute', top: 78, width: '100%', textAlign: 'center'}}>Votre caviste à Rezé</Libelle>
			<Img
				src={staticFile('logo_cave71_transparent.png')}
				style={{position: 'absolute', top: 112, left: (LARGEUR - 640) / 2, width: 640}}
			/>

			{/* Accroche */}
			<div
				style={{
					position: 'absolute',
					top: 318,
					width: '100%',
					textAlign: 'center',
					fontFamily: SERIF,
					fontStyle: 'italic',
					fontWeight: 500,
					fontSize: 60,
					lineHeight: 1,
					color: C.creme,
				}}
			>
				Vins, spiritueux <span style={{color: C.or}}>&</span> épicerie fine
			</div>
			<Libelle style={{position: 'absolute', top: 392, width: '100%', textAlign: 'center', color: C.orPale, letterSpacing: 5, fontSize: 12.5}}>
				Domaines · Distilleries · Artisans du terroir
			</Libelle>

			{/* Voûte de cave */}
			<svg width={LARGEUR} height={HAUTEUR} style={{position: 'absolute', inset: 0}}>
				<defs>
					<linearGradient id="voute" x1="0" y1="0" x2="0" y2="1">
						<stop offset="0" stopColor={C.or} stopOpacity={0.9} />
						<stop offset="1" stopColor={C.or} stopOpacity={0.15} />
					</linearGradient>
				</defs>
				<path
					d={`M 90 ${ETAGERE_Y} L 90 760 A 530 330 0 0 1 1150 760 L 1150 ${ETAGERE_Y}`}
					fill="none"
					stroke="url(#voute)"
					strokeWidth={1.6}
				/>
				<path
					d={`M 104 ${ETAGERE_Y} L 104 762 A 516 318 0 0 1 1136 762 L 1136 ${ETAGERE_Y}`}
					fill="none"
					stroke="url(#voute)"
					strokeWidth={0.7}
					opacity={0.6}
				/>
			</svg>

			{/* Étagère */}
			<div
				style={{
					position: 'absolute',
					left: 60,
					right: 60,
					top: ETAGERE_Y,
					height: 150,
					background: 'linear-gradient(to bottom, rgba(90,30,44,0.6), rgba(20,16,18,0) 90%)',
					WebkitMaskImage: 'linear-gradient(to right, transparent, black 18%, black 82%, transparent)',
					maskImage: 'linear-gradient(to right, transparent, black 18%, black 82%, transparent)',
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: 60,
					right: 60,
					top: ETAGERE_Y,
					height: 1,
					background: 'linear-gradient(to right, rgba(230,207,152,0), rgba(230,207,152,0.7) 25%, rgba(230,207,152,0.7) 75%, rgba(230,207,152,0))',
				}}
			/>

			{BOUTEILLES.map((b) => (
				<Produit key={b.src} {...b} base={ETAGERE_Y} reflet={0.22} />
			))}
			{TERRINES.map((t) => (
				<Produit key={t.src} {...t} base={PREMIER_PLAN_Y} reflet={0.16} />
			))}

			{/* Services */}
			<div style={{position: 'absolute', top: 1246, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 22}}>
				<div style={{width: 120, height: 1, background: C.or, opacity: 0.6}} />
				<Libelle>À la Cave 71</Libelle>
				<div style={{width: 120, height: 1, background: C.or, opacity: 0.6}} />
			</div>
			<div
				style={{
					position: 'absolute',
					top: 1292,
					left: 90,
					right: 90,
					display: 'flex',
					flexWrap: 'wrap',
					justifyContent: 'center',
					rowGap: 26,
				}}
			>
				{SERVICES.map((s) => (
					<div key={s.titre} style={{width: 353, display: 'flex', alignItems: 'center', gap: 16}}>
						<div
							style={{
								width: 58,
								height: 58,
								flexShrink: 0,
								borderRadius: '50%',
								border: `1px solid rgba(207,165,72,0.6)`,
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
							}}
						>
							<Icone nom={s.icone} />
						</div>
						<div style={{lineHeight: 1.18}}>
							<div style={{fontFamily: SERIF, fontWeight: 600, fontSize: 27, color: C.creme}}>{s.titre}</div>
							<div style={{fontFamily: SERIF, fontStyle: 'italic', fontSize: 23, color: C.orPale}}>{s.suite}</div>
						</div>
					</div>
				))}
			</div>

			{/* Pied : infos pratiques */}
			<div style={{position: 'absolute', top: 1490, left: 90, right: 90, height: 1, background: `linear-gradient(to right, rgba(207,165,72,0), ${C.or}, rgba(207,165,72,0))`}} />
			<div style={{position: 'absolute', top: 1516, left: 90, right: 90, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
				<div style={{width: 330}}>
					<Libelle>Nous trouver</Libelle>
					<div style={{fontFamily: SERIF, fontSize: 30, fontWeight: 600, marginTop: 10, lineHeight: 1.1}}>
						71 avenue de la Libération
						<br />
						44400 Rezé
					</div>
					<div style={{fontSize: 14, color: C.orPale, marginTop: 10, lineHeight: 1.4}}>
						En face du parking et du tram du 8 Mai
					</div>
				</div>
				<div style={{width: 360, textAlign: 'center'}}>
					<Libelle>Du mardi au samedi</Libelle>
					<div style={{fontFamily: SERIF, fontSize: 30, fontWeight: 600, marginTop: 10, lineHeight: 1.1}}>
						10h – 13h <span style={{color: C.or}}>·</span> 15h30 – 19h30
					</div>
					<div style={{fontFamily: SANS, fontWeight: 600, fontSize: 30, letterSpacing: 2, color: C.creme, marginTop: 14}}>02 49 62 66 45</div>
				</div>
				<div style={{width: 300, display: 'flex', gap: 16, justifyContent: 'flex-end', alignItems: 'flex-start'}}>
					<div style={{textAlign: 'right', fontSize: 14.5, lineHeight: 1.75}}>
						<Libelle style={{marginBottom: 4}}>En ligne</Libelle>
						<div style={{fontWeight: 600, fontSize: 17}}>cave71.com</div>
						<div>contact.cave71@gmail.com</div>
						<div>Facebook : Cave 71</div>
					</div>
					<div style={{background: C.creme, padding: 7, borderRadius: 4}}>
						<Img src={staticFile('qr_cave71.svg')} style={{width: 92, height: 92, display: 'block'}} />
					</div>
				</div>
			</div>

			{/* Mention légale */}
			<div
				style={{
					position: 'absolute',
					bottom: 52,
					width: '100%',
					textAlign: 'center',
					fontSize: 12.5,
					letterSpacing: 0.4,
					color: 'rgba(244,236,224,0.72)',
				}}
			>
				L’abus d’alcool est dangereux pour la santé, à consommer avec modération.
			</div>
		</AbsoluteFill>
	);
};
