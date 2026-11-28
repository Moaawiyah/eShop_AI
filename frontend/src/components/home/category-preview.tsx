import {
  CameraIcon,
  GamepadIcon,
  HeadphonesIcon,
  HouseIcon,
  LaptopIcon,
  SmartphoneIcon,
  type LucideIcon,
} from "lucide-react";

const CATEGORIES: readonly { name: string; Icon: LucideIcon }[] = [
  { name: "Phones", Icon: SmartphoneIcon },
  { name: "Laptops", Icon: LaptopIcon },
  { name: "Audio", Icon: HeadphonesIcon },
  { name: "Cameras", Icon: CameraIcon },
  { name: "Gaming", Icon: GamepadIcon },
  { name: "Smart home", Icon: HouseIcon },
];

/** Static, non-interactive preview; the real catalog arrives in a later milestone. */
export function CategoryPreview() {
  return (
    <section
      id="categories"
      aria-labelledby="categories-heading"
      className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6"
    >
      <h2 id="categories-heading" className="text-title font-semibold">
        Categories
      </h2>
      <p className="mt-2 max-w-xl text-muted-foreground">
        A preview of what the catalog will cover. Browsing is coming soon.
      </p>
      <ul className="mt-8 grid grid-cols-1 gap-4 min-[420px]:grid-cols-2 lg:grid-cols-3">
        {CATEGORIES.map(({ name, Icon }) => (
          <li
            key={name}
            className="flex items-center gap-4 rounded-2xl border bg-card p-5 text-card-foreground"
          >
            <span className="flex size-11 items-center justify-center rounded-xl bg-accent text-accent-foreground">
              <Icon className="size-5" aria-hidden="true" />
            </span>
            <span className="flex flex-col">
              <span className="font-medium">{name}</span>
              <span className="text-sm text-muted-foreground">Coming soon</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
