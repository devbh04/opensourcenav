import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ owner: string; repo: string }> }
) {
  try {
    const resolvedParams = await params;
    const { owner, repo } = resolvedParams;
    const repo_name = `${owner}/${repo}`;

    const client = await clientPromise;
    const db = client.db(process.env.MONGODB_DB_NAME || "repodocify");
    const col = db.collection("docs");

    const doc = await col.findOne(
      { repo_name },
      { projection: { "pages.content_md": 0, _id: 0 } }
    );

    if (!doc) {
      return NextResponse.json(
        { detail: `No docs found for ${repo_name}` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      repo_name: doc.repo_name,
      repo_url: doc.repo_url,
      generated_at: doc.generated_at,
      meta: doc.meta || {},
      stats: doc.stats || {},
      page_slugs: doc.pages ? doc.pages.map((p: any) => p.slug) : [],
    });
  } catch (error) {
    console.error("Failed to fetch doc meta:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
