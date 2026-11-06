import React from 'react';
import DocumentIngestionBar from '../components/DocumentIngestionBar';
export default function DocumentsView() {
  return <section style={{maxWidth:1100,margin:'0 auto'}}><header style={{marginBottom:22}}><h1>Gestion documentaire</h1><p>Importez et g?rez les documents de r?f?rence de l?assistant RAG.</p></header><DocumentIngestionBar /></section>;
}
