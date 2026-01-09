import Card from "@/components/card";

export default function Page() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card
        title="Alphonso"
        description="Loved worldwide for their sweetness our Alphonso mangoes are a delicious delight wherever you are."
        price={270}
        imageSrc="/mango.jpg"
        discount="20% off"
        badges={[{ label: "Best Seller" }]}
        stockLeft={9}
      />
    </main>
  );
}
