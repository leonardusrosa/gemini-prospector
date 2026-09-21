export type Lead = {
  slug: string;
  nome: string | null;
  nicho: string | null;
  cidade: string | null;
  nota: number | null;
  avaliacoes: number | null;
  email: string | null;
  telefone: string | null;
  whatsapp: string | null;
  siteAntigo: string | null;
  motivo: string | null;
  status: string | null;
  urlNova: string | null;
  candidateUrl: string | null;
  liveUrl: string | null;
  proposalUrl: string | null;
  dataProposta: string | null;
  valor: number | null;
  obs: string | null;
  contratoStatus: string | null;
  contratoEm: string | null;
  manutencao: number | null;
  pago: number | null;
  docCliente: string | null;
  endCliente: string | null;
  atualizado: string | null;
  placeId: string | null;
  opportunityType: string | null;
  opportunityScore: number | null;
  classificationEvidence: string | null;
  mainRisk: string | null;
  factualContent: string | null;
  imageryLevel: string | null;
  socialUrls: string | null;
  mapsUrl: string | null;
  runId: number | null;
  criadoEm: string | null;
  country: string | null;
  locale: string | null;
  language: string | null;
  phoneCountryCode: string | null;
  websiteStatus: string | null;
  siteMode: string | null;
  currency: string | null;
  marketTier: string | null;
};

export type OutreachHistory = {
  id: number;
  slug: string;
  canal: string;
  destino: string | null;
  tipo: string | null;
  mensagem: string | null;
  urlProposta: string | null;
  mensagemId: string | null;
  status: string | null;
  criadoEm: string | null;
};

export type LeadUpdate = Partial<Pick<Lead,
  | "status"
  | "obs"
  | "contratoStatus"
  | "contratoEm"
  | "manutencao"
  | "pago"
  | "docCliente"
  | "endCliente"
  | "valor"
  | "dataProposta"
  | "candidateUrl"
  | "liveUrl"
  | "proposalUrl"
>>;
