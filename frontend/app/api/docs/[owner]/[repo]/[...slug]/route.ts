import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ owner: string; repo: string; slug: string[] }> }
) {
  try {
    const resolvedParams = await params;
    const { owner, repo, slug } = resolvedParams;
    const repo_name = `${owner}/${repo}`;
    const target_slug = slug.join("/").replace(/^\/|\/$/g, ""); // Strip leading/trailing slashes

    const client = await clientPromise;
    const db = client.db(process.env.MONGODB_DB_NAME || "repodocify");
    const col = db.collection("docs");

    const doc = await col.findOne({ repo_name }, { projection: { _id: 0 } });

    if (!doc) {
      return NextResponse.json(
        { detail: `No docs found for ${repo_name}` },
        { status: 404 }
      );
    }

    const pages = doc.pages || [];
    let foundPage = null;

    for (const page of pages) {
      if (page.slug.replace(/^\/|\/$/g, "") === target_slug) {
        foundPage = page;
        break;
      }
    }

    if (!foundPage) {
      return NextResponse.json(
        { detail: `Page '${target_slug}' not found` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      page: foundPage,
      meta: doc.meta || {},
      repo_name,
    });
  } catch (error) {
    console.error("Failed to fetch doc page:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
