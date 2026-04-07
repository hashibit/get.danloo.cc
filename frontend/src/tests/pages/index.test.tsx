import React from "react";
import Home from "../../pages/index";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock next/link component
const MockLink = ({ children, href }: { children: React.ReactNode; href: string }) => (
  <a href={href}>{children}</a>
);
MockLink.displayName = 'MockLink';

jest.mock("next/link", () => MockLink);

// Mock the Header component
const MockHeader = () => <header data-testid="mock-header">Header</header>;
MockHeader.displayName = 'MockHeader';

jest.mock("../../components/Header", () => MockHeader);

describe("Home Page", () => {
  it("renders the main title", () => {
    render(<Home />);
    expect(screen.getByText("Stay curious.")).toBeInTheDocument();
  });

  it("renders the subtitle", () => {
    render(<Home />);
    expect(
      screen.getByText(
        "Discover stories, thinking, and expertise from writers on any topic.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the start reading link", () => {
    render(<Home />);
    const startReadingLink = screen.getByText("Start reading");
    expect(startReadingLink).toBeInTheDocument();
    expect(startReadingLink).toHaveAttribute("href", "/my-dashboard");
  });

  it("renders all three feature sections", () => {
    render(<Home />);

    // Upload Materials feature
    expect(screen.getByText("Upload Materials")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Upload dialogue records, PDF documents, or text notes as materials for AI processing.",
      ),
    ).toBeInTheDocument();

    // AI Processing feature
    expect(screen.getByText("AI Processing")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Our AI algorithms extract and refine technical knowledge from your content.",
      ),
    ).toBeInTheDocument();

    // Golden Pills feature
    expect(screen.getByText("Golden Pills")).toBeInTheDocument();
    expect(
      screen.getByText(
        'Transform your materials into valuable "丹" (golden pills) pellets.',
      ),
    ).toBeInTheDocument();
  });

  it("renders the call to action section", () => {
    render(<Home />);
    expect(screen.getByText("Ready to dive deeper?")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Join thousands of readers who turn to 丹炉 for reliable insights and fresh perspectives.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the Get started link", () => {
    render(<Home />);
    const getStartedLink = screen.getByText("Get started");
    expect(getStartedLink).toBeInTheDocument();
    expect(getStartedLink).toHaveAttribute("href", "/my-dashboard");
  });

  it("renders the Browse pellets link", () => {
    render(<Home />);
    const browsePelletsLink = screen.getByText("Browse pellets");
    expect(browsePelletsLink).toBeInTheDocument();
    expect(browsePelletsLink).toHaveAttribute("href", "/pellets");
  });

  it("matches snapshot", () => {
    const { container } = render(<Home />);
    expect(container).toMatchSnapshot();
  });
});
