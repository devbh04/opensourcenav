"use client";

import { useState, useEffect } from "react";
import mermaid from "mermaid";

interface MermaidDiagramProps {
  chart: string;
}

export const MermaidDiagram = ({ chart }: MermaidDiagramProps) => {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const renderChart = async () => {
      try {
        mermaid.initialize({
          startOnLoad: true,
          theme: "dark",
          themeVariables: {
            primaryColor: "#3b82f6",
            primaryTextColor: "#e2e8f0",
            primaryBorderColor: "#475569",
            lineColor: "#64748b",
            sectionBkgColor: "#1e293b",
            altSectionBkgColor: "#334155",
            gridColor: "#475569",
            secondaryColor: "#4338ca",
            tertiaryColor: "#7c3aed",
          },
        });

        const { svg } = await mermaid.render(`mermaid-${Date.now()}`, chart);
        setSvg(svg);
        setError("");
      } catch (err) {
        setError(
          `Mermaid Error: ${err instanceof Error ? err.message : String(err)}`
        );
        console.error("Mermaid rendering error:", err);
      }
    };

    renderChart();
  }, [chart]);

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 mb-4">
        <p className="text-red-300 text-sm font-mono">{error}</p>
      </div>
    );
  }

  return (
    <div
      className="mermaid-diagram bg-slate-800/50 rounded-lg p-4 mb-4 flex justify-center"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
