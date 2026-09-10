export interface ServiceItem {
  number: string;
  title: string;
  description: string;
}

export interface ReviewItem {
  id: string;
  quote: string;
  author: string;
  tag: string;
  serviceFocus: string;
  rating: number;
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
    id: "review-01",
    quote:
      "Had my Tacoma detailed yesterday. Long story short it turned out beautiful. Wilson and his team did an amazing job. I fully recommend this establishment. These guys are awesome and you get every penny’s worth of the price.",
    author: "Kevin K",
    tag: "Public Review",
    serviceFocus: "Tacoma Full Detail",
    rating: 5,
  },
  {
    id: "review-02",
    quote:
      "Wilson and team did an awesome job! They removed very deep scratches on my car for a fair price. I had gone to other dealers and they gave me much higher quotes. I received excellent customer service, price and great results.",
    author: "Marlene Olmos",
    tag: "Public Review",
    serviceFocus: "Deep Scratch Removal",
    rating: 5,
  },
  {
    id: "review-03",
    quote:
      "Wilson and his team were great. I called for a full detail and he gave me a great price. They made my car look brand new. Overall, great customer service and I 100% recommend this company to anyone needing work done.",
    author: "Vanessa Ballard",
    tag: "Public Review",
    serviceFocus: "Full Vehicle Detail",
    rating: 5,
  },
  {
    id: "review-04",
    quote:
      "I am beyond happy! Wilson was nothing short of amazing! I pulled in on Monday and he got me in the next day. Did everything from engine bay to interior. He even cleaned the wheels and brake calipers! Car looks brand new.",
    author: "Tyler",
    tag: "Public Review",
    serviceFocus: "Engine Bay & Calipers",
    rating: 5,
  },
  {
    id: "review-05",
    quote:
      "Our vehicle was used for work driving through limestone mines for years and was covered in stone dust inside and out. Wilson and his team did a phenomenal job leaving it practically like new. Their expertise is truly a work of art.",
    author: "Kevin Denhof",
    tag: "Public Review",
    serviceFocus: "Heavy Dust & Interior",
    rating: 5,
  },
  {
    id: "review-06",
    quote:
      "Wilson and his team made my 9-year-old Range Rover and 12-year-old M3 look brand new inside, outside, and under the hood! Fantastic customer service and results better than expected. Trust Wilson to take care of all my vehicles.",
    author: "Ian Thomas",
    tag: "Public Review",
    serviceFocus: "Multi-Car Detailing",
    rating: 5,
  },
  {
    id: "review-07",
    quote:
      "Hands down the best detailing and buffing in Dallas! Wilson was extremely careful and understanding with how I care for my vehicle. He shows utmost professionalism and kindness. A customer for life.",
    author: "Jay",
    tag: "Public Review",
    serviceFocus: "Detailing & Buffing",
    rating: 5,
  },
  {
    id: "review-08",
    quote:
      "DD&B did a fantastic touch-up job on some deep scratches in the fiberglass. Most shops insist on repainting and blending the entire panel, but this team did incredible and precise work. Highly recommended!",
    author: "Josh T",
    tag: "Public Review",
    serviceFocus: "Precision Touch-Up",
    rating: 5,
  },
  {
    id: "review-09",
    quote:
      "Wilson did a phenomenal job on my GLK. Incredibly professional, left my car looking brand new. Nothing was overlooked and the engine bay is spotless. He has earned my loyalty for years to come.",
    author: "Brian Stephenson",
    tag: "Public Review",
    serviceFocus: "GLK Detail & Engine",
    rating: 5,
  },
  {
    id: "review-10",
    quote:
      "Brought my truck in for buffing after it got water spots and scratches caused by poor quality products. Wilson and his team made it look brand new. Left very grateful and will definitely be back!",
    author: "Jackson Maxey",
    tag: "Public Review",
    serviceFocus: "Water Spot & Scratch Removal",
    rating: 5,
  },
  {
    id: "review-11",
    quote:
      "Great price, great work, great customer service! Wilson and his team did clay bar decontamination, buffing, and ceramic coating on my Camry. Now it looks better than when I bought it!",
    author: "Caleb",
    tag: "Public Review",
    serviceFocus: "Clay Bar & Ceramic Coating",
    rating: 5,
  },
  {
    id: "review-12",
    quote:
      "Had my headlights restored here, and Wilson was amazing. Fair price, very friendly, and did a great job. Came here based on reviews and was not disappointed. Highly recommend this place!",
    author: "Abdullah F",
    tag: "Public Review",
    serviceFocus: "Headlight Restoration",
    rating: 5,
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
    src: "/assets/gallery/gallery-01-studio-porsche-cayenne.webp",
    alt: "Porsche Cayenne inside Addison detailing studio on checkered floor under ceiling LED light bars",
    width: 1179,
    height: 861,
    category: "Studio Facility",
  },
  {
    id: "gallery-02",
    src: "/assets/gallery/gallery-02-rolls-royce-gloss-finish.webp",
    alt: "Deep black Rolls Royce clearcoat finished to high gloss reflection",
    width: 1600,
    height: 1600,
    category: "High Gloss Finish",
  },
  {
    id: "gallery-03",
    src: "/assets/gallery/gallery-03-gmc-sierra-heavy-duty.webp",
    alt: "White GMC Sierra truck with detailed paint and mirror-polished chrome",
    width: 1600,
    height: 1200,
    category: "Exterior Detail",
  },
  {
    id: "gallery-04",
    src: "/assets/gallery/gallery-04-acura-mdx-exterior-service.webp",
    alt: "White Acura MDX detailed outside the shop with detailing equipment",
    width: 1600,
    height: 1473,
    category: "Vehicle Delivery",
  },
  {
    id: "gallery-05",
    src: "/assets/gallery/gallery-05-interior-cockpit-restoration.webp",
    alt: "Restored driver cockpit, dashboard, and clean floor mats",
    width: 1200,
    height: 1600,
    category: "Interior Cockpit",
  },
  {
    id: "gallery-06",
    src: "/assets/gallery/gallery-06-red-metallic-paint-reflection.webp",
    alt: "Red metallic paint panel polished to clean optical reflection",
    width: 1600,
    height: 1200,
    category: "Surface Correction",
  },
  {
    id: "gallery-07",
    src: "/assets/gallery/gallery-07-leather-interior-reconditioning.webp",
    alt: "Cleaned and conditioned light gray leather rear vehicle seating",
    width: 1200,
    height: 1600,
    category: "Leather Care",
  },
  {
    id: "gallery-08",
    src: "/assets/gallery/gallery-08-instrument-cluster-precision.webp",
    alt: "Dust-free vehicle instrument gauges and dash cluster detail",
    width: 1600,
    height: 1205,
    category: "Precision Detail",
  },
];
