import React from 'react';
import {Still} from 'remotion';
import {Panneau, LARGEUR, HAUTEUR} from './Panneau';

// A1 portrait (594 x 841 mm). Export x2.829 = 3508 x 4962 px, 150 dpi.
export const RemotionRoot: React.FC = () => (
	<>
		<Still id="Panneau" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: true}} />
		{/* Fond sans texte ni logo, pour le PPTX modifiable */}
		<Still id="PanneauFond" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: false}} />
	</>
);
