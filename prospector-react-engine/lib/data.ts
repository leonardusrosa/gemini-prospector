import { assetPath } from "@/lib/site-paths";

export interface ServiceItem {
  number: string;
  title: string;
  description: string;
}

export interface ReviewItem {
  id: string;
  nativeReviewId: string;
  fingerprint: string;
  quote: string;
  author: string;
  tag: string;
  serviceFocus: string;
  rating: number;
  translationState: "ORIGINAL" | "SURFACE_TRANSLATED";
  sourceLocale: string;
}

export const BUSINESS_INFO = {
  name: "Dallas Detailing And Buffing",
  leadSpecialist: "Wilson",
  address: "16284 Midway Rd, Addison, TX 75001",
  phone: "+1 214-400-7287",
  phoneDisplay: "(214) 400-7287",
  rating: 4.9,
  reviewCount: 268,
  cityState: "Addison, TX",
} as const;

export const SERVICES_LIST: ServiceItem[] = [
  {
    number: "01",
    title: "PAINT CORRECTION & BUFFING",
    description: "Paint correction and buffing services.",
  },
  {
    number: "02",
    title: "COLOR SANDING",
    description: "Color sanding services for automotive paint surfaces.",
  },
  {
    number: "03",
    title: "FULL AUTO DETAILING",
    description: "Interior and exterior auto detailing.",
  },
  {
    number: "04",
    title: "HEADLIGHT RESTORATION",
    description: "Headlight restoration services.",
  },
  {
    number: "05",
    title: "ENGINE BAY DETAILING",
    description: "Engine bay detailing.",
  },
  {
    number: "06",
    title: "WHEEL & BRAKE CALIPER CARE",
    description: "Wheel and brake caliper cleaning and detailing.",
  },
];

export const PUBLIC_REVIEWS: ReviewItem[] = [
  {
    id: "google-review-kevin-k",
    nativeReviewId: "Ci9DQUlRQUNvZENodHljRjlvT2twMGQwVnhRelJJTUZsSldHTjJWRWhYWm13MlkxRRAB",
    fingerprint: "eb77e273b5a1b6b6c0721584741b29cdc3a315fa2e9be2e9fbb8d575c3db5c0d",
    quote:
      "Had my Tacoma detailed yesterday. Long story short it turned out beautiful. Wilson and his team did an amazing job. I fully recommend this establishment. These guys are awesome and you get every penny’s worth of the price. In the famous words if Arnold: ILL BE BACK !",
    author: "Kevin K",
    tag: "Public Review",
    serviceFocus: "Tacoma Detail",
    rating: 5,
    translationState: "ORIGINAL",
    sourceLocale: "en-US",
  },
  {
    id: "google-review-marlene-olmos",
    nativeReviewId: "Ci9DQUlRQUNvZENodHljRjlvT21FNWMyMUxiMGhpWXpaS1UzQTRTRFZQVTAwNFdsRRAB",
    fingerprint: "81181d0f04d1e0647939c8c1b0a99d63f4c1a331ab4719db3afa1c0b392bdfe8",
    quote:
      "Wilson and team did an awesome job! They removed very deep scratches on my car for a fair price. I had gone to other dealers and they gave me much higher quotes. I do not regret my decision of taking my car here as I received excellent customer service, price and great results as you can see in the pics before and after.",
    author: "Marlene Olmos",
    tag: "Public Review",
    serviceFocus: "Deep Scratches",
    rating: 5,
    translationState: "ORIGINAL",
    sourceLocale: "en-US",
  },
  {
    id: "google-review-vanessa-ballard",
    nativeReviewId: "ChdDSUhNMG9nS0VJQ0FnTURJMGM2ZGl3RRAB",
    fingerprint: "503ec8635c8f7d0995273eba0f6a24880cbed2456c0d2e7d43305dd6f6e784d2",
    quote:
      "Wilson and his team were great. I called for a full detail and he gave me a great price. They made my car look brand new. Overall, great customer service and I 100% recommend this company to anyone needing work done to their vehicle... Thanks again Wilson, I truly appreciate you for taking car of my car!",
    author: "Vanessa Ballard",
    tag: "Public Review",
    serviceFocus: "Full Detail",
    rating: 5,
    translationState: "ORIGINAL",
    sourceLocale: "en-US",
  },
  {
    id: "google-review-tyler",
    nativeReviewId: "ChZDSUhNMG9nS0VJQ0FnTUN3cnVQUlpBEAE",
    fingerprint: "e7c7ae7fe9f66aed1f9cd7ff16d175e87c57d9d05dea6b56d40fc665ccb160e7",
    quote:
      "I am beyond happy!! Wilson was nothing short of amazing! I pulled in on Monday and he was able to get me in the next day! I ended up doing everything from engine bay to interior and I couldn’t be happier! ... He even cleaned the wheels and brake calipers! Car looks brand new! ...",
    author: "Tyler",
    tag: "Public Review",
    serviceFocus: "Engine Bay, Interior & Calipers",
    rating: 5,
    translationState: "ORIGINAL",
    sourceLocale: "en-US",
  },
  {
    id: "google-review-0",
    nativeReviewId: "Ci9DQUlRQUNvZENodHljRjlvT2t4c2J6UTFjV1ZYZG5oTGNVbHVaWEJwVXpaMlZtYxAB",
    fingerprint: "dd9d98427ba55c09c1bdfde1be8661625de3c3418516ba6cd32530fe20b468b5",
    quote:
      "Nosso filho usou nosso veículo para trabalhar, dirigindo por minas de calcário no Missouri durante anos. O veículo estava coberto de poeira e sujeira de pedra, tanto por dentro quanto por fora. Wilson e sua equipe fizeram um trabalho fenomenal, não apenas limpando o carro, mas deixando-o praticamente como novo. A expertise deles é verdadeiramente uma obra de arte.",
    author: "Kevin Denhof",
    tag: "Public Review",
    serviceFocus: "Interior & Exterior Cleaning",
    rating: 5,
    translationState: "SURFACE_TRANSLATED",
    sourceLocale: "unknown",
  },
  {
    id: "google-review-5",
    nativeReviewId: "ChdDSUhNMG9nS0VJQ0FnTUR3c01iSXJ3RRAB",
    fingerprint: "22ee8b6dd56131e4fe9e10d10813eb1f3107983541c1a72b27156e2416744b77",
    quote:
      "Minha namorada (Toyota Camry 2016) sofreu uma pequena colisão que danificou o para-lama direito e quebrou o suporte e o para-choque. Pesquisamos orçamentos em toda a região norte de Dallas e optamos pelo Wilson, da Dallas Detailing and Buffing. Ele não só nos ofereceu o melhor preço para o conserto (80% do segundo maior orçamento e menos da metade do maior), como o atendimento foi impecável. Ele nos explicou todo o processo, detalhando exatamente o que queríamos fazer e onde cada centavo seria gasto. Optamos por usar peças de reposição para economizar, incluindo a troca e pintura do para-lama, a troca e pintura do para-choque, a troca do suporte e o alinhamento da porta com o para-lama. A comunicação durante todo o processo foi excelente; o Wilson me manteve informado em cada etapa até a conclusão do serviço. Quando pegamos o carro de volta, ele parecia novo em folha! Menor preço, excelente mão de obra e um profissional confiável. Se eu precisar de reparos na lataria novamente, eles serão minha primeira opção!",
    author: "Jameson Mantzel",
    tag: "Public Review",
    serviceFocus: "Fender & Bumper Repair",
    rating: 5,
    translationState: "SURFACE_TRANSLATED",
    sourceLocale: "unknown",
  },
  {
    id: "google-review-6",
    nativeReviewId: "Ci9DQUlRQUNvZENodHljRjlvT25wak5EaDZPV2htUTFJd1JXTTJWMGxOYTJwMmVsRRAB",
    fingerprint: "bebdcb255c2ef0bc0eecf6855451a853c0cd2e6a5cbf1cd093dff5f79751dfba",
    quote:
      "Recomendo muito este lugar para detalhamento automotivo interno na região metropolitana de Dallas-Fort Worth! Sem dúvida, o melhor lugar de todos!! 🥇\n\nLevamos nosso SUV hoje para um detalhamento interno e fiquei impressionado com os resultados. Quando o buscamos, o interior do carro parecia novo. A equipe prestou atenção a cada detalhe e fez um trabalho incrível. Eles até removeram os adesivos dos vidros traseiros que minha filha havia colocado. Sinceramente, achei que seria impossível removê-los, mas eles fizeram isso perfeitamente, sem deixar nenhum resíduo.\n\nO interior ficou impecável, com um aspecto fresco e profissionalmente limpo, e o SUV ficou pronto muito mais rápido do que esperávamos, o que foi uma ótima surpresa.\n\nNa verdade, moramos em North Fort Worth e dirigimos até Addison porque confiamos no Wilson e em sua equipe, e mais uma vez eles não decepcionaram. O preço foi muito razoável para a qualidade do trabalho que eles oferecem.\n\nSe você está procurando por um serviço de detalhamento automotivo interno de alta qualidade em Addison ou em qualquer lugar na região metropolitana de Dallas-Fort Worth, recomendo muito o Wilson e sua equipe. Com certeza voltaremos!",
    author: "Jo",
    tag: "Public Review",
    serviceFocus: "Interior Detailing",
    rating: 5,
    translationState: "SURFACE_TRANSLATED",
    sourceLocale: "unknown",
  },
  {
    id: "google-review-7",
    nativeReviewId: "ChdDSUhNMG9nS0VJQ0FnSURjOHNqWXF3RRAB",
    fingerprint: "9b52110ddb0f1801e4e2f0cc8caf819cc49087b568a5e314f5d9deef290d3ae3",
    quote:
      "A Dallas Detailing and Buffing é incrível!\n\nO Wilson e sua equipe deixaram meu Range Rover de 9 anos e meu M3 de 12 anos com aparência de novos – por dentro, por fora e debaixo do capô! E ambos os veículos precisavam de MUITO cuidado antes do serviço.\n\nAtendimento ao cliente fantástico e resultados melhores do que o esperado! Voltarei sempre que precisar da ajuda do Wilson e sua equipe.\n\n*Atualização de março de 2024: A DD&B continua fazendo um ótimo trabalho! Deixaram meu Range Rover com uma aparência ótima NOVAMENTE, e meu Outback está melhor do que novo depois de um polimento e revestimento cerâmico!\n\nConfio no Wilson e sua equipe para cuidar de todos os meus veículos!\n\n*Atualização de fevereiro de 2026: A DD&B deixou meu Xterra de 24 anos com uma aparência fantástica! Este carro precisava de muita atenção, e o Wilson o fez brilhar! O interior parece novo!",
    author: "Ian Thomas",
    tag: "Public Review",
    serviceFocus: "Buffing & Ceramic Coating",
    rating: 5,
    translationState: "SURFACE_TRANSLATED",
    sourceLocale: "unknown",
  },
];

export interface GalleryMediaItem {
  id: string;
  src: string;
  alt: string;
  width: number;
  height: number;
  category: string;
}

export const GALLERY_MEDIA: GalleryMediaItem[] = [
  {
    id: "gallery-01",
    src: assetPath("gallery/gallery-01-studio-porsche-cayenne.webp"),
    alt: "White Porsche Cayenne inside a garage work area on a checkered floor",
    width: 1179,
    height: 861,
    category: "Vehicle Indoors",
  },
  {
    id: "gallery-02",
    src: assetPath("gallery/gallery-02-rolls-royce-gloss-finish.webp"),
    alt: "Black Rolls-Royce parked outdoors with reflections visible on the bodywork",
    width: 1600,
    height: 1600,
    category: "Vehicle Exterior",
  },
  {
    id: "gallery-03",
    src: assetPath("gallery/gallery-03-gmc-sierra-heavy-duty.webp"),
    alt: "White GMC Sierra pickup parked outdoors",
    width: 1600,
    height: 1200,
    category: "Pickup Exterior",
  },
  {
    id: "gallery-04",
    src: assetPath("gallery/gallery-04-acura-mdx-exterior-service.webp"),
    alt: "White Acura MDX outside a commercial building",
    width: 1600,
    height: 1473,
    category: "Vehicle Exterior",
  },
  {
    id: "gallery-05",
    src: assetPath("gallery/gallery-05-interior-cockpit-restoration.webp"),
    alt: "Vehicle front interior with steering wheel, dashboard, and seats",
    width: 1200,
    height: 1600,
    category: "Vehicle Interior",
  },
  {
    id: "gallery-06",
    src: assetPath("gallery/gallery-06-red-metallic-paint-reflection.webp"),
    alt: "Red painted vehicle surface under reflected lighting",
    width: 1600,
    height: 1200,
    category: "Paint Surface",
  },
  {
    id: "gallery-07",
    src: assetPath("gallery/gallery-07-leather-interior-reconditioning.webp"),
    alt: "Light gray fabric rear seats with the vehicle doors open",
    width: 1200,
    height: 1600,
    category: "Rear Interior",
  },
  {
    id: "gallery-08",
    src: assetPath("gallery/gallery-08-instrument-cluster-precision.webp"),
    alt: "Vehicle instrument cluster and gauges behind the steering wheel",
    width: 1600,
    height: 1205,
    category: "Instrument Cluster",
  },
];
