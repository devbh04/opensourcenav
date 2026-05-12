import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const skip = parseInt(searchParams.get("skip") || "0", 10);
    const limit = parseInt(searchParams.get("limit") || "16", 10);
    
    if (limit <= 0 || limit > 50) {
      return NextResponse.json({ error: "Limit must be between 1 and 50" }, { status: 400 });
    }

    const client = await clientPromise;
    const db = client.db(process.env.MONGODB_DB_NAME || "repodocify");
    const col = db.collection("docs");

    const total = await col.countDocuments({});
    const cursor = col
      .find(
        {},
        {
          projection: {
            repo_name: 1,
            repo_url: 1,
            generated_at: 1,
            stats: 1,
            "meta.stats": 1,
            _id: 0,
          },
        }
      )
      .sort({ generated_at: -1 })
      .skip(skip)
      .limit(limit);

    const docsRaw = await cursor.toArray();

    const docs = docsRaw.map((doc: any) => {
      const stats = doc.stats || (doc.meta && doc.meta.stats) || {};
      return {
        repo_name: doc.repo_name || "",
        repo_url: doc.repo_url || "",
        generated_at: doc.generated_at || "",
        page_count: stats.pages_generated || 0,
        languages: stats.languages || [],
      };
    });

    return NextResponse.json({ docs, total, skip, limit });
  } catch (error) {
    console.error("Failed to fetch docs:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
