export const VisibilityIcon = ({ visible = true }: { visible?: boolean }) => (
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="w-5 h-5"
  >
    {visible ? (
      <>
        <path
          d="M12 5C7 5 2.73 8.11 1 12.5C2.73 16.89 7 20 12 20C17 20 21.27 16.89 23 12.5C21.27 8.11 17 5 12 5Z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <circle
          cx="12"
          cy="12.5"
          r="3.5"
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
        />
      </>
    ) : (
      <>
        <path
          d="M3 3L21 21"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path
          d="M10.5 10.7C9.9 11.3 9.5 12.1 9.5 13C9.5 14.7 10.8 16 12.5 16C13.4 16 14.2 15.6 14.8 15"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M6.6 6.6C4.3 8.1 2.5 10.3 1.5 13C3.2 17.4 7.5 20.5 12.5 20.5C14.6 20.5 16.6 19.9 18.3 18.9"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M19.5 16.2C21.1 14.8 22.4 13 23 11C21.3 6.6 17 3.5 12 3.5C11.1 3.5 10.2 3.6 9.4 3.8"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
      </>
    )}
  </svg>
);
