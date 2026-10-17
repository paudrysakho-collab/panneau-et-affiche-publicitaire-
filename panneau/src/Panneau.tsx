import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Img, continueRender, delayRender, staticFile} from 'remotion';
import textes from './textes.json';

// Stop-trottoir A1 portrait (594 x 841 mm). Toile 1240 x 1754 px, export x2.829 = 3508 x 4962 px (150 dpi).
// Les textes (src/textes.json) sont volontairement grands : lisibles à quelques mètres sur le trottoir.
export const LARGEUR = 1240;
export const HAUTEUR = 1754;

// Palettes du stop-trottoir. Mêmes noms de couleurs, autres valeurs : les textes de src/textes.json
// désignent « or », « creme »… et suivent la palette choisie.
//   photo : la photo de groupe recolorée pour ce fond (tools/photo_couleur.py, tools/photo_claire_finale.py)
//   halo  : les trois arrêts du dégradé radial derrière les produits, et sa taille
export type Palette = {
	encre: string;
	vin: string;
	bordeaux: string;
	or: string;
	orPale: string;
	creme: string;
	cremeDoux: string;
	photo: Cle;
	halo: [string, string, string];
	haloTaille: string;
};

// Version sombre : le lie-de-vin de la photo studio, prolongé sur toute l'affiche.
export const C: Record<string, string> = {
	encre: '#0f0405',
	vin: '#4a1a20',
	bordeaux: '#7d1530',
	or: '#cfa548',
	orPale: '#e6cf98',
	creme: '#f4ece0',
	cremeDoux: 'rgba(244,236,224,0.72)',
};

// Version claire : le blanc chaud de la photo studio.
export const CLAIR: Record<string, string> = {
	encre: '#f3ebe1',
	vin: '#fbf7f1',
	bordeaux: '#7d1530',
	or: '#a77a26',
	orPale: '#7d1530',
	creme: '#2a1619',
	cremeDoux: 'rgba(42,22,25,0.68)',
};

export const PALETTES: Record<string, Palette> = {
	// 1. lie-de-vin : la version validée, sobre et chic
	sombre: {...C, photo: 'sombre', halo: ['#4a1a20', '#2a0c10', 'rgba(15,4,5,0)'], haloTaille: '820px 760px'} as Palette,
	// 2. crème : la plus lisible en plein jour, sur un trottoir gris
	clair: {...CLAIR, photo: 'clair', halo: ['#fbf7f1', '#f5eee5', 'rgba(234,221,204,0.9)'], haloTaille: '900px 900px'} as Palette,
	// 3. grenat : le même monde du vin, mais un rouge vif qui se voit de loin
	grenat: {
		encre: '#1a0509',
		vin: '#8a1a2c',
		bordeaux: '#7d1530',
		or: '#eac470',
		orPale: '#f6e3b0',
		creme: '#fff7ec',
		cremeDoux: 'rgba(255,247,236,0.76)',
		photo: 'grenat',
		halo: ['#8a1a2c', '#4a0d18', 'rgba(26,5,9,0)'],
		haloTaille: '860px 790px',
	},
	// 4. vert bouteille : très « cave », et le verre ambré des bouteilles y ressort
	vert: {
		encre: '#04100a',
		vin: '#12452c',
		bordeaux: '#7d1530',
		or: '#dcb75e',
		orPale: '#efe0aa',
		creme: '#f5f2e6',
		cremeDoux: 'rgba(245,242,230,0.74)',
		photo: 'vert',
		halo: ['#12452c', '#0a2418', 'rgba(4,16,10,0)'],
		haloTaille: '840px 770px',
	},
	// 5. bleu nuit : le fond froid qui fait le plus ressortir l'or et l'ambre
	bleu: {
		encre: '#030a12',
		vin: '#143353',
		bordeaux: '#7d1530',
		or: '#e2bc63',
		orPale: '#f1dfa9',
		creme: '#f1f3ef',
		cremeDoux: 'rgba(241,243,239,0.74)',
		photo: 'bleu',
		halo: ['#143353', '#0a1c2f', 'rgba(3,10,18,0)'],
		haloTaille: '840px 770px',
	},
	// 6. safran : fond clair et chaud, texte bordeaux — chaleureux et très visible
	safran: {
		encre: '#eeb63f',
		vin: '#fbdf99',
		bordeaux: '#7d1530',
		or: '#8c2213',
		orPale: '#9c3a1c',
		creme: '#2a1108',
		cremeDoux: 'rgba(42,17,8,0.74)',
		photo: 'safran',
		halo: ['#fbdf99', '#f2c45c', 'rgba(226,163,42,0.95)'],
		haloTaille: '900px 900px',
	},
	// 7. pourpre 71 : la couleur du « 71 » du logo (#701028) tenue sur toute l'affiche, en profond
	pourpre: {
		encre: '#1b0611',
		vin: '#731a44',
		bordeaux: '#7d1530',
		or: '#e3bd6e',
		orPale: '#f2e0b2',
		creme: '#fdf4ec',
		cremeDoux: 'rgba(253,244,236,0.76)',
		photo: 'pourpre',
		halo: ['#731a44', '#3d0c24', 'rgba(27,6,17,0)'],
		haloTaille: '860px 790px',
	},
	// 8. violet : le même pourpre tiré vers le violet franc, clair et vif
	violet: {
		encre: '#ae63c2',
		vin: '#d9a7e6',
		bordeaux: '#7d1530',
		or: '#4a1054',
		orPale: '#5d1a69',
		creme: '#2b0b31',
		cremeDoux: 'rgba(43,11,49,0.74)',
		photo: 'violet',
		halo: ['#d9a7e6', '#be78cf', 'rgba(158,78,180,0.95)'],
		haloTaille: '900px 900px',
	},
	// 9. parme : le violet du 71 en lilas clair, le plus lumineux des trois
	parme: {
		encre: '#d7b6e6',
		vin: '#eddcf5',
		bordeaux: '#7d1530',
		or: '#6b2070',
		orPale: '#7e3184',
		creme: '#33103a',
		cremeDoux: 'rgba(51,16,58,0.74)',
		photo: 'parme',
		halo: ['#eddcf5', '#ddc0ea', 'rgba(198,160,219,0.95)'],
		haloTaille: '900px 900px',
	},
	// 10. corail : le plus chaud, impossible à rater sur un trottoir gris
	corail: {
		encre: '#f0836a',
		vin: '#fbb59f',
		bordeaux: '#7d1530',
		or: '#73162a',
		orPale: '#8c2a36',
		creme: '#3b0f10',
		cremeDoux: 'rgba(59,15,16,0.74)',
		photo: 'corail',
		halo: ['#fbb59f', '#f29070', 'rgba(224,106,74,0.95)'],
		haloTaille: '900px 900px',
	},
	// 11. anis : vert tendre et frais, côté épicerie fine et produits du terroir
	anis: {
		encre: '#c3d94f',
		vin: '#e4f09c',
		bordeaux: '#7d1530',
		or: '#45610f',
		orPale: '#55731a',
		creme: '#1e2b06',
		cremeDoux: 'rgba(30,43,6,0.74)',
		photo: 'anis',
		halo: ['#e4f09c', '#cbe063', 'rgba(176,200,58,0.95)'],
		haloTaille: '900px 900px',
	},
	// 12. turquoise : la couleur la plus opposée à l'ambre des bouteilles, donc celle qui les fait ressortir
	turquoise: {
		encre: '#5fc6cf',
		vin: '#aee6ea',
		bordeaux: '#7d1530',
		or: '#0d555e',
		orPale: '#136872',
		creme: '#07262a',
		cremeDoux: 'rgba(7,38,42,0.74)',
		photo: 'turquoise',
		halo: ['#aee6ea', '#74ccd4', 'rgba(62,174,186,0.95)'],
		haloTaille: '900px 900px',
	},
	// 13. framboise : clair et gai, du côté des rosés
	framboise: {
		encre: '#ef7f9e',
		vin: '#fbb3c5',
		bordeaux: '#7d1530',
		or: '#7d1738',
		orPale: '#9a2448',
		creme: '#3a0a1c',
		cremeDoux: 'rgba(58,10,28,0.74)',
		photo: 'framboise',
		halo: ['#fbb3c5', '#f293ab', 'rgba(226,99,133,0.95)'],
		haloTaille: '900px 900px',
	},
};

const SERIF = "'Cormorant Garamond', serif";
const SANS = "'Montserrat', sans-serif";

// Photo studio Gemini (bouteilles, jus, terrines, chocolat), fondue dans le fond par des bords en dégradé.
const PHOTO = {x: 20, y: 408, w: 1200};
// proportions de chaque photo (largeur / hauteur), et décalage vertical pour centrer la plus basse
// w : largeur affichée (sinon PHOTO.w), h : hauteur imposée (photo plus haute que large : centrée, moins large),
// cote : fondu à gauche et à droite (%), bas : début du fondu du bas (%)
type Cle =
	| 'sombre'
	| 'clair'
	| 'grenat'
	| 'vert'
	| 'bleu'
	| 'safran'
	| 'pourpre'
	| 'violet'
	| 'parme'
	| 'corail'
	| 'anis'
	| 'turquoise'
	| 'framboise'
	| 'vitrine'
	| 'rangee'
	| 'gradins';
const PHOTOS: Record<Cle, {src: string; ratio: number; dy: number; haut: number; cote?: number; h?: number; bas?: number}> = {
	// photo de groupe validée par le client (13 produits sur la marche noire, sol brillant)
	sombre: {src: 'photo_finale_sombre.jpg', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	clair: {src: 'photo_finale_claire.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	// la même photo, son décor repeint pour les autres fonds (même cadrage, mêmes réglages)
	grenat: {src: 'photo_finale_grenat.jpg', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	vert: {src: 'photo_finale_vert.jpg', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	bleu: {src: 'photo_finale_bleu.jpg', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	safran: {src: 'photo_finale_safran.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	pourpre: {src: 'photo_finale_pourpre.jpg', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	violet: {src: 'photo_finale_violet.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	parme: {src: 'photo_finale_parme.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	corail: {src: 'photo_finale_corail.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	anis: {src: 'photo_finale_anis.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	turquoise: {src: 'photo_finale_turquoise.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	framboise: {src: 'photo_finale_framboise.png', ratio: 1672 / 941, dy: 2, haut: 5, cote: 4, bas: 72},
	// ancienne photo (ChatGPT v15 aux étiquettes recollées), gardée pour comparaison
	vitrine: {src: 'vitrine_sombre.jpg', ratio: 1693 / 929, dy: 8, haut: 6},
	// photos composées à partir des vrais produits détourés (tools/compose_produits.py)
	rangee: {src: 'compo_rangee_sombre.png', ratio: 4142 / 2139, dy: 22, haut: 1, cote: 2.5},
	gradins: {src: 'compo_gradins_sombre.png', ratio: 3562 / 2568, dy: 4, haut: 1, cote: 2.5, h: 664},
};
const taillePhoto = (c: Cle) => {
	const p = PHOTOS[c];
	const w = p.h ? p.h * p.ratio : PHOTO.w;
	return {w, h: w / p.ratio, x: (LARGEUR - w) / 2, y: PHOTO.y + p.dy};
};

// Icônes des services : une par colonne, au-dessus des blocs service-1..5 de textes.json.
const ICONES = ['cadeau', 'verres', 'bouteille', 'carte', 'alliances'].map((nom, i) => ({nom, x: 180 + 220 * i - 31, y: 1140}));

const Icone: React.FC<{nom: string; couleur: string}> = ({nom, couleur}) => {
	const trait = {fill: 'none', stroke: couleur, strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
	return (
		<svg width={38} height={38} viewBox="0 0 32 32">
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
				chargees.forEach((p) => (document.fonts as unknown as {add: (f: FontFace) => void}).add(p));
				continueRender(handle);
			})
			.catch((e) => {
				console.error(e);
				continueRender(handle);
			});
	}, [handle]);
	return null;
};

type Segment = {t: string; police: string; taille: number; graisse?: number; italique?: boolean; couleur: string; espacement?: number};
type Bloc = {id: string; x: number; y: number; w: number; align: string; interligne?: number; lignes: Segment[][]};

const BlocTexte: React.FC<{bloc: Bloc; K: Palette}> = ({bloc, K}) => (
	<div
		style={{
			position: 'absolute',
			left: bloc.x,
			top: bloc.y,
			width: bloc.w,
			textAlign: bloc.align as React.CSSProperties['textAlign'],
			lineHeight: bloc.interligne ?? 1.2,
			zIndex: 20,
		}}
	>
		{bloc.lignes.map((ligne, i) => (
			<div key={i} style={{whiteSpace: 'nowrap'}}>
				{ligne.map((s, j) => (
					<span
						key={j}
						style={{
							fontFamily: s.police === 'serif' ? SERIF : SANS,
							fontSize: s.taille,
							fontWeight: s.graisse ?? 400,
							fontStyle: s.italique ? 'italic' : 'normal',
							color: (K as unknown as Record<string, string>)[s.couleur] ?? s.couleur,
							letterSpacing: s.espacement ?? 0,
						}}
					>
						{s.t}
					</span>
				))}
			</div>
		))}
	</div>
);

const Photo: React.FC<{cle: Cle}> = ({cle}) => {
	const {src, haut, cote = 5, bas = 92} = PHOTOS[cle];
	const {x, y, w, h} = taillePhoto(cle);
	const fondu = `linear-gradient(to right, transparent, black ${cote}%, black ${100 - cote}%, transparent), linear-gradient(to bottom, transparent, black ${haut}%, black ${bas}%, transparent)`;
	return (
		<Img
			src={staticFile(`produits/${src}`)}
			style={{position: 'absolute', left: x, top: y, width: w, height: h, WebkitMaskImage: fondu, maskImage: fondu, WebkitMaskComposite: 'source-in', maskComposite: 'intersect'}}
		/>
	);
};

export const Panneau: React.FC<{texte?: boolean; clair?: boolean; photo?: Cle; palette?: string}> = ({
	texte = true,
	clair = false,
	photo,
	palette,
}) => {
	const P = PALETTES[palette ?? (clair ? 'clair' : 'sombre')];
	const K = P;
	const cle: Cle = photo ?? P.photo;
	const tp = taillePhoto(cle);
	const centreY = ((tp.y + tp.h / 2) / HAUTEUR) * 100;
	return (
		<AbsoluteFill style={{background: K.encre, color: K.creme, fontFamily: SANS, overflow: 'hidden', fontVariantNumeric: 'lining-nums'}}>
			<Polices />

			{/* Fond : halo assorti à celui de la photo, centré sur les produits */}
			<AbsoluteFill
				style={{
					background: `radial-gradient(ellipse ${P.haloTaille} at 50% ${centreY}%, ${P.halo[0]} 0%, ${P.halo[1]} ${
						P.haloTaille === '900px 900px' ? 45 : 40
					}%, ${P.halo[2]} ${P.haloTaille === '900px 900px' ? 100 : 85}%)`,
				}}
			/>

			{/* Grain léger */}
			<svg width={LARGEUR} height={HAUTEUR} style={{position: 'absolute', inset: 0, opacity: 0.07, mixBlendMode: 'overlay'}}>
				<filter id="grain">
					<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} stitchTiles="stitch" />
				</filter>
				<rect width="100%" height="100%" filter="url(#grain)" />
			</svg>

			<Photo cle={cle} />

			{/* Double filet doré */}
			<div style={{position: 'absolute', inset: 26, border: `1.5px solid ${K.or}`, opacity: 0.85}} />
			<div style={{position: 'absolute', inset: 34, border: `0.75px solid ${K.or}`, opacity: 0.45}} />

			{/* Logo officiel, couleurs jamais modifiées : CAVE blanc, 71 bordeaux, sur son bloc noir. */}
			{texte && <Img src={staticFile('logo_cave71_bloc.png')} style={{position: 'absolute', top: 98, left: (LARGEUR - 760) / 2, width: 760}} />}

			{/* Filets autour du titre des services */}
			<div style={{position: 'absolute', top: 1106, left: 250, width: 230, height: 1, background: K.or, opacity: 0.6}} />
			<div style={{position: 'absolute', top: 1106, left: 760, width: 230, height: 1, background: K.or, opacity: 0.6}} />

			{ICONES.map((i) => (
				<div
					key={i.nom}
					style={{
						position: 'absolute',
						left: i.x,
						top: i.y,
						width: 62,
						height: 62,
						borderRadius: '50%',
						border: `1px solid ${K.or}`,
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
					}}
				>
					<Icone nom={i.nom} couleur={K.or} />
				</div>
			))}

			{/* Pied : grille 2 x 2 (adresse | horaires / en ligne | QR code) séparée par des filets dorés */}
			<div style={{position: 'absolute', top: 1336, left: 60, right: 60, height: 1, background: `linear-gradient(to right, transparent, ${K.or}, transparent)`}} />
			<div style={{position: 'absolute', top: 1508, left: 70, right: 70, height: 1, background: K.or, opacity: 0.35}} />
			<div style={{position: 'absolute', top: 1356, bottom: 1754 - 1660, left: 635, width: 1, background: K.or, opacity: 0.35}} />
			<div style={{position: 'absolute', top: 1522, left: 698, background: '#fff', padding: 8, borderRadius: 4}}>
				<Img src={staticFile('qr_cave71.svg')} style={{width: 120, height: 120, display: 'block'}} />
			</div>

			{texte && (textes.blocs as Bloc[]).map((b) => <BlocTexte key={b.id} bloc={b} K={K} />)}
		</AbsoluteFill>
	);
};
