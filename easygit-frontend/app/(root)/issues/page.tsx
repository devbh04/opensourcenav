"use client"

import * as React from "react"
import { PageHeader } from "@/components/issues/page-header"
import { IssueFilterForm } from "@/components/issues/issue-filter-form"
import { IssueTable } from "@/components/issues/issue-table"
import { ErrorDisplay } from "@/components/issues/error-display"
import { useIssueStore } from "@/store/issue-store"

export default function IssuesPage() {
  const { error } = useIssueStore()

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        <PageHeader
          title="Issue Analyzer"
          description="Analyze GitHub repository issues to find good first issues, bugs, and feature requests"
        />

        <div className="space-y-8">
          <IssueFilterForm />
          
          {error && (
            <ErrorDisplay message={error} />
          )}
          
          <IssueTable />
        </div>
      </div>
    </div>
  )
}
