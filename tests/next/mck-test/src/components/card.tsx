// app/components/Card.tsx
"use client";

import { motion, type Variants } from "framer-motion";
import Image from "next/image";

const cardVariants: Variants = {
  initial: {
    opacity: 0,
    y: 24,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.16, 1, 0.3, 1], // ✅ easing válido y tipado
    },
  },
  hover: {
    scale: 1.02,
  },
};

const backgroundVariants: Variants = {
  light: {
    backgroundColor: "#ffffff",
    color: "#111827",
  },
  highlight: {
    background:
      "linear-gradient(180deg, #facc15 0%, #ca8a04 100%)",
    color: "#ffffff",
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

type Badge = { label: string };

type CardProps = {
  title: string;
  description: string;
  price: number;
  imageSrc: string;
  discount?: string;
  badges?: Badge[];
  stockLeft?: number;
};

export default function Card({
  title,
  description,
  price,
  imageSrc,
  discount,
  badges = [],
  stockLeft,
}: CardProps) {
  return (
    <motion.article
      variants={cardVariants}
      initial="initial"
      animate="visible"
      whileHover="hover"
      className="w-[320px] rounded-[28px] shadow-xl overflow-hidden cursor-pointer"
    >
      <motion.div
        variants={backgroundVariants}
        initial="light"
        whileHover="highlight"
        className="h-full"
      >
        <div className="relative p-4">
          {discount && (
            <span className="absolute top-4 left-4 rounded-full bg-black/20 px-3 py-1 text-xs text-white">
              {discount}
            </span>
          )}

          <Image
            src={imageSrc}
            alt={title}
            width={260}
            height={260}
            className="mx-auto rounded-2xl object-cover"
          />
        </div>

        <div className="px-6 pb-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">{title}</h3>
            <span className="rounded-full bg-black/20 px-3 py-1 text-sm font-medium">
              ₹{price}
            </span>
          </div>

          <p className="mt-2 text-sm opacity-90">{description}</p>

          <div className="mt-4 flex gap-2">
            {badges.map((b) => (
              <span
                key={b.label}
                className="rounded-full bg-black/10 px-3 py-1 text-xs font-medium"
              >
                {b.label}
              </span>
            ))}
            {stockLeft !== undefined && (
              <span className="rounded-full bg-black/10 px-3 py-1 text-xs font-medium">
                {stockLeft} left
              </span>
            )}
          </div>

          <motion.button
            whileTap={{ scale: 0.97 }}
            className="mt-6 w-full rounded-full py-3 font-semibold bg-[#4b332d] text-white"
          >
            Add to cart
          </motion.button>
        </div>
      </motion.div>
    </motion.article>
  );
}
