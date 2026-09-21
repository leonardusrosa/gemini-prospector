import React from "react";
import { BUSINESS_INFO } from "@/lib/data";

export function LocationSection() {
  return (
    <section
      id="studio"
      data-motion="reveal"
      className="w-full py-24 md:py-32 bg-[#0f1217] text-white border-t border-white/[0.06] overflow-hidden"
    >
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Left Column: Oversized Address & Direct Action */}
          <div className="lg:col-span-5 flex flex-col justify-between">
            <div>
              <div className="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[#caa35d] mb-4">
                <span>[ 05 — STUDIO LOCATION ]</span>
                <div className="h-[1px] w-6 bg-[#caa35d]/40" />
              </div>

              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold font-display uppercase tracking-tight leading-tight text-white">
                {BUSINESS_INFO.address.split(",")[0]}
              </h2>

              <p className="mt-3 text-lg text-neutral-300 font-light">
                {BUSINESS_INFO.cityState} 75001 • United States
              </p>

              <p className="mt-6 text-base text-neutral-300 font-light leading-relaxed max-w-md">
                Automotive detailing, buffing, and surface care in Addison, Texas. Inquiries and service scheduling handled directly with Wilson.
              </p>
            </div>

            {/* Hairline Divider & Contact Trigger */}
            <div className="mt-10 relative pt-8">
              <div className="absolute top-0 inset-x-0 h-[1px] bg-white/10" />

              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
                <a
                  href={`tel:${BUSINESS_INFO.phone}`}
                  className="inline-flex items-center justify-center gap-4 px-8 py-4 bg-[#caa35d] text-black font-bold text-xs tracking-[0.15em] uppercase hover:bg-[#dcba78] transition-all transform active:scale-95 shadow-xl rounded-sm"
                >
                  <span>Call {BUSINESS_INFO.phoneDisplay}</span>
                  <span>→</span>
                </a>
                <div className="text-xs text-neutral-400 uppercase tracking-widest font-mono">
                  Midway Corridor • Addison TX
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Architectural Frame for Map */}
          <div className="lg:col-span-7 w-full h-[360px] sm:h-[420px] rounded-sm overflow-hidden border border-white/10 relative shadow-2xl bg-[#080a0d]">
            <iframe
              title="Dallas Detailing And Buffing Location in Addison TX"
              width="100%"
              height="100%"
              style={{ border: 0, filter: "grayscale(100%) invert(92%) contrast(85%)" }}
              loading="lazy"
              allowFullScreen
              referrerPolicy="no-referrer-when-downgrade"
              src="https://maps.google.com/maps?q=16284+Midway+Rd,+Addison,+TX+75001&t=&z=15&ie=UTF8&iwloc=&output=embed"
            />
            <div className="absolute top-4 right-4 bg-[#08090b]/90 backdrop-blur-md px-3 py-1.5 border border-white/10 text-[10px] font-mono uppercase tracking-widest text-[#caa35d]">
              Addison Studio
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
