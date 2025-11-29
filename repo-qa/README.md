```markdown
# Unstopclone: A Platform for Opportunities and Growth

## 1. Project Title & Description

**Unstopclone** is a Next.js web application inspired by the Unstop platform, designed to connect users with opportunities in various fields, including internships, mentorships, hackathons, and courses. It prioritizes a custom and accessible user interface, robust form handling, and features like a code editor. Built with modern web development technologies, Unstopclone aims to provide a seamless and engaging experience for users seeking to enhance their skills and career prospects.

## 2. Features

Unstopclone offers a wide range of features, including:

*   **User Authentication:** Secure signup and sign-in functionality with password management (forgot password, reset password).
*   **Profile Management:** User profile pages for viewing and editing personal information, along with the ability to track registered/posted items (courses, hackathons, internships, mentors). Role-based access (Recruiter, Mentor, Admin) is implemented.
*   **Opportunity Listings:**
    *   **Internships:** Browse and search internships, view detailed internship information, apply for internships via a multi-step application form, and post internship opportunities (for recruiters).
    *   **Mentorships:** Browse and search mentors, view mentor profiles, request mentorship, and register as a mentor.
    *   **Hackathons:** Browse and search hackathons, view detailed hackathon information, register for hackathons, and host hackathons (for organizers).
    *   **Courses:** Browse and search courses, view detailed course information, and enroll in courses.
*   **Admin Panel:** Admin-specific features for managing courses, including uploading new courses and viewing registered candidates.
*   **Code Editor:** An integrated code editor (Monaco Editor) for practicing coding skills and submitting solutions to coding problems.
*   **Quiz System:** Domain-based quiz to test users' knowledge.
*   **Search & Filtering:** Robust search and filtering capabilities across different opportunity listings.
*   **Responsive Design:** A fully responsive user interface that adapts to different screen sizes.
*   **Accessibility:**  Emphasis on accessibility using Radix UI primitives and semantic HTML.
*   **Theming:** Support for light and dark themes.
*   **Notifications:** Real-time notifications using `sonner`.

## 3. Architecture & Structure

The project follows a modular architecture, leveraging Next.js's file-based routing and component-based structure. Here's a breakdown of the key directories and files:

*   **`app/`:**  The Next.js app directory, containing all routes and UI components.
    *   **`(root)/`:** Contains the main application routes, requiring authentication.
        *   **`admin/`:** Routes accessible only to administrators.
            *   `admin-courses/`: Admin course management page
            *   `course-upload/`: Admin course upload page
            *   `layout.tsx`: Admin authentication guard.
        *   **`blog/`:** Blog listing page.
        *   **`courses/[id]/`:** Course details page.
        *   **`hackathon/[id]/`:** Hackathon details page.
        *   **`hackathon/hackathon-reg/[id]/`:** Hackathon Registration page.
        *   **`host-opportunity/`:** Host Hackathon Form
        *   **`internship/[id]/`:** Internship details page.
        *   **`internship/[id]/applying-page/`:** Internship application page.
        *   **`mentorship/[id]/`:** Mentor details page.
        *   **`mentorship/mentor-registration/`:** Mentor registration page.
        *   **`profile/`:** User profile page.
        *   `profile/profile-internships/[id]/`: Page to view candidates for user's internship
        *   `profile/profile-mentorships/[id]/`: Page to view candidates for user's mentorship
        *   `profile/profile-hackathons/[id]/`: Page to view teams for user's hackathon
        *   `courses/`: Course listing page
        *   `courses/find-courses/`: Page to search courses
        *   `hackathon/`: Hackathon listing page
        *   `internship/`: Internship listing page
        *   `internship/find-internship/`: Page to search internships
        *   `mentorship/`: Mentorship listing page
        *   `domain/`: Domain selection page for quizzes
        *   `quiz/`: Quiz page
        *   `page.tsx`: Home page.
        *   `layout.tsx`: Root layout with authentication check.
    *   **`(auth)/`:** Authentication routes (signup, signin, forgot password, reset password).
        *   `signup/`: Signup page.
        *   `signin/`: Signin page.
        *   `forgot-password/`: Forgot password page.
        *   `reset-password/[id]/`: Reset password page.
    *   **`editor/`:** Code editor page.
    *   `layout.tsx`: Root layout (global styles, fonts, analytics).
*   **`components/`:** Reusable UI components.
    *   `ui/`: Styled UI components (Radix UI + Tailwind CSS).
    *   `carousel.tsx`: Carousel component.
    *   `carouselslider-*.tsx`: Carousel sliders for courses, hackathons, mentors, and internships.
    *   `form.tsx`: Form components.
    *   `resetPassword.tsx`: Modal dialog to reset password.
    *   `appbar.tsx`: Application navigation bar.
    *   `footer.tsx`: Application footer.
    *   `interncategorycard.tsx`: Internship category card
    *   `numberscard.tsx`: Card displaying numerical values.
    *   `OptionCard.tsx`: clickable card with image and text.
    *   `HackathonCard.tsx`: Card displaying hackathon data.
    *   `CourseCategoryCard.tsx`: Card displaying course category.
    *   `MentorCard.tsx`: Card displaying mentor data.
    *   `CompetitionCard.tsx`: Card displaying competition data.
    *   `CourseCard.tsx`: Card displaying course data.
    *   `InternshipCard.tsx`: Card displaying internship data.
    *   `ProfileCategoryCard.tsx`: Card displaying profile category.
*   **`lib/`:** Utility functions and constants.
    *   `constants.ts`: Defines the base API URL.
    *   `utils.ts`: Utility functions (e.g., `cn` for class name merging).
    *   `codePS.js`: Coding problem statements.
*   **`store/`:** Zustand stores for state management.
    *    `signUpStore.js`: Zustand store for user registration, login and logout
    *    `internshipStore.js`: Zustand store for managing list of internships and draft internship object
*   **`public/`:** Static assets (images, fonts, etc.).
*   **`package.json`:** Project dependencies and scripts.
*   **`package-lock.json`:** Dependency lock file.
*   **`next.config.js`:** Next.js configuration file.
*   **`tsconfig.json`:** TypeScript configuration file.
*   **`components.json`:** Shadcn UI configuration file.

## 4. Installation & Setup

Follow these steps to set up the project locally:

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd unstopclone
    ```

2.  **Install dependencies:**

    ```bash
    npm install  # or yarn install or pnpm install
    ```

3.  **Configure environment variables:**

    *   Create a `.env.local` file in the root directory.
    *   Define the necessary environment variables (see "Configuration" section below).

4.  **Run the development server:**

    ```bash
    npm run dev  # or yarn dev or pnpm dev
    ```

    This will start the Next.js development server, typically accessible at `http://localhost:3000`.

## 5. Usage

Once the development server is running, you can access the application in your browser.

*   **Sign up or sign in:** Navigate to `/signup` or `/signin` to create an account or log in.
*   **Browse opportunities:** Explore internships, mentorships, hackathons, and courses on their respective pages.
*   **Manage your profile:**  View and edit your profile information at `/profile`.
*   **Admin access:** Navigate to `/admin` to access the admin panel (requires admin credentials).

## 6. API/Endpoints (if applicable)

The application interacts with a backend API for data fetching and persistence. The base URL for the API is defined in `lib/constants.ts`. Specific API endpoints are used for:

*   **Authentication:**
    *   `/api/signup`: User registration.
    *   `/api/signin`: User authentication.
    *   `/api/forgot-password`: Request password reset.
    *   `/api/reset-password`: Reset password.
*   **Opportunities (Internships, Mentorships, Hackathons, Courses):**
    *   `/api/internships`: Fetch internships, create internships.
    *   `/api/mentorships`: Fetch mentors, register as a mentor.
    *   `/api/hackathons`: Fetch hackathons, host hackathons.
    *   `/api/courses`: Fetch courses, create courses.
*   **User Data:**
    *   `/api/user`: Fetch and update user profile information.

**Note:** The exact API endpoints and data formats may vary depending on the backend implementation.

## 7. Configuration

The following environment variables are required for the application to run correctly:

*   `NEXT_PUBLIC_UMAMI_ID`: The ID of the Umami analytics instance.
*   `NEXT_PUBLIC_UMAMI_DOMAIN`: The domain of the Umami analytics instance.
*   `NEXT_PUBLIC_BASE_URL`: The base URL of the backend API.
*   `NEXTAUTH_SECRET`: Secret for NextAuth.
*   `NEXTAUTH_URL`: The URL for NextAuth.
*   `GOOGLE_CLIENT_ID`: Google Client ID for authentication.
*   `GOOGLE_CLIENT_SECRET`: Google Client Secret for authentication.

These variables should be defined in a `.env.local` file in the root directory.  For example:

```
NEXT_PUBLIC_UMAMI_ID=your_umami_id
NEXT_PUBLIC_UMAMI_DOMAIN=your_umami_domain.com
NEXT_PUBLIC_BASE_URL=https://api.example.com
NEXTAUTH_SECRET=your_very_long_and_secure_secret
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

```

## 8. Contributing

We welcome contributions to Unstopclone! If you'd like to contribute, please follow these steps:

1.  **Fork the repository.**
2.  **Create a new branch for your feature or bug fix:**

    ```bash
    git checkout -b feature/your-feature-name
    ```

3.  **Make your changes and commit them:**

    ```bash
    git add .
    git commit -m "Add: Your descriptive commit message"
    ```

4.  **Push your branch to your forked repository:**

    ```bash
    git push origin feature/your-feature-name
    ```

5.  **Create a pull request to the main branch of the original repository.**

Please ensure that your code follows the project's coding style and includes appropriate tests.
```