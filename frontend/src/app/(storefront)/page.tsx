import type { Metadata } from "next";

import { CategoryPreview } from "@/components/home/category-preview";
import { HeroSection } from "@/components/home/hero-section";

// An absolute title avoids the "%s · eShop_AI" template on the home page.
export const metadata: Metadata = {
  title: { absolute: "eShop_AI · Electronics storefront demo" },
};

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <CategoryPreview />
    </>
  );
}
