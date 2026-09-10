import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { Services } from "@/components/Services";
import { CompareSlider } from "@/components/CompareSlider";
import { Reviews } from "@/components/Reviews";
import { GallerySection } from "@/components/GallerySection";
import { LocationSection } from "@/components/LocationSection";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#08090b] text-[#f0f2f5] font-sans antialiased selection:bg-[#caa35d] selection:text-[#08090b]">
      <Navbar />
      <Hero />
      <Services />
      <CompareSlider />
      <Reviews />
      <GallerySection />
      <LocationSection />
      <Footer />
    </main>
  );
}
