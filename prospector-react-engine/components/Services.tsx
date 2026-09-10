import React from "react";
import { SERVICES_LIST } from "@/lib/data";

export function Services() {
  const tier1Services = SERVICES_LIST.slice(0, 3);
  const tier2Services = SERVICES_LIST.slice(3, 6);

  return (
    <section
      id="services"
      className="w-full py-24 md:py-32 bg-[#0f1217] text-white border-t border-white/[0.06] overflow-hidden"
    >
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16">
        {/* Section Header */}
        <div className="max-w-3xl mb-16 md:mb-24">
          <div className="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[#caa35d] mb-4">
            <span>[ 01 — SERVICES ]</span>
            <div className="h-[1px] w-6 bg-[#caa35d]/40" />
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-display uppercase tracking-tight leading-tight">
            TECHNICAL DETAILING SERVICES
          </h2>
          <p className="mt-5 text-base sm:text-lg text-neutral-300 font-light leading-relaxed max-w-2xl">
            Auto detailing, paint correction, buffing, and automotive surface care performed by Wilson in Addison, Texas.
          </p>
        </div>

        {/* Tier 1: Asymmetric Spread (Vertical Macro Crop Left + Services 01-03 Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-center mb-20 lg:mb-28">
          {/* Major Photographic Moment 1: Vertical Paint Detail Crop */}
          <div className="lg:col-span-5 relative w-full aspect-[4/5] sm:aspect-[3/4] overflow-hidden bg-[#0a0c10]">
            <img
              src="/assets/service-paint-detail.webp"
              alt="Multistage automotive paint correction reflection on deep clearcoat"
              loading="lazy"
              decoding="async"
              className="w-full h-full object-cover object-center grayscale-[20%] hover:grayscale-0 transition-all duration-700 hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0f1217] via-transparent to-black/30 pointer-events-none" />
            <div className="absolute bottom-4 left-5 right-5 flex justify-between items-end text-[10px] uppercase tracking-[0.2em] text-neutral-400 font-mono pointer-events-none">
              <span>Macro Surface Polish</span>
            </div>
          </div>

          {/* Services 01 - 03 Column */}
          <div className="lg:col-span-7 flex flex-col">
            {tier1Services.map((service) => (
              <div
                key={service.number}
                className="group relative py-8 sm:py-9 transition-all duration-300 hover:pl-2"
              >
                {/* Hairline horizontal separator */}
                <div className="absolute top-0 inset-x-0 h-[1px] bg-white/10" />

                <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 sm:gap-6 items-baseline">
                  <div className="sm:col-span-2 flex items-baseline">
                    <span className="text-sm sm:text-base font-mono font-semibold text-[#caa35d] opacity-90 group-hover:opacity-100">
                      {service.number}
                    </span>
                  </div>
                  <div className="sm:col-span-5">
                    <h3 className="text-lg sm:text-xl font-bold font-display tracking-tight text-white group-hover:text-[#caa35d] transition-colors uppercase">
                      {service.title}
                    </h3>
                  </div>
                  <div className="sm:col-span-5">
                    <p className="text-sm sm:text-base text-neutral-300 font-light leading-relaxed">
                      {service.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            <div className="h-[1px] w-full bg-white/10" />
          </div>
        </div>

        {/* Tier 2: Inverted Editorial Spread (Services 04-06 Left + Wide Studio Finish Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 items-center">
          {/* Services 04 - 06 Column */}
          <div className="lg:col-span-7 flex flex-col order-2 lg:order-1">
            {tier2Services.map((service) => (
              <div
                key={service.number}
                className="group relative py-8 sm:py-9 transition-all duration-300 hover:pl-2"
              >
                {/* Hairline horizontal separator */}
                <div className="absolute top-0 inset-x-0 h-[1px] bg-white/10" />

                <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 sm:gap-6 items-baseline">
                  <div className="sm:col-span-2 flex items-baseline">
                    <span className="text-sm sm:text-base font-mono font-semibold text-[#caa35d] opacity-90 group-hover:opacity-100">
                      {service.number}
                    </span>
                  </div>
                  <div className="sm:col-span-5">
                    <h3 className="text-lg sm:text-xl font-bold font-display tracking-tight text-white group-hover:text-[#caa35d] transition-colors uppercase">
                      {service.title}
                    </h3>
                  </div>
                  <div className="sm:col-span-5">
                    <p className="text-sm sm:text-base text-neutral-300 font-light leading-relaxed">
                      {service.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            <div className="h-[1px] w-full bg-white/10" />
          </div>

          {/* Major Photographic Moment 2: Wide Studio Finish Crop */}
          <div className="lg:col-span-5 relative w-full aspect-[16/10] sm:aspect-[16/10] overflow-hidden bg-[#0a0c10] order-1 lg:order-2">
            <img
              src="/assets/service-finish-wide.webp"
              alt="Automotive detailing precision finish with linear overhead reflection"
              loading="lazy"
              decoding="async"
              className="w-full h-full object-cover object-center grayscale-[15%] hover:grayscale-0 transition-all duration-700 hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0f1217] via-transparent to-black/30 pointer-events-none" />
            <div className="absolute bottom-4 left-5 right-5 flex justify-between items-end text-[10px] uppercase tracking-[0.2em] text-neutral-400 font-mono pointer-events-none">
              <span>Studio Refinement</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
