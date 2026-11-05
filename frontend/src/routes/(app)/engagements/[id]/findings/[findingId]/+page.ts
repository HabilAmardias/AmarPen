export function load({ params }: { params: { id: string; findingId: string } }) {
  return { id: params.id, findingId: params.findingId };
}
