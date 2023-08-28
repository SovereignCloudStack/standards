import React from "react";
import styles from "./button.module.css";

interface ButtonProps {
    title: string;
    href?: string;
    handleClick: (e: any) => void;
}

const Button: React.FunctionComponent<ButtonProps> = (props) => {
    const { title, href, handleClick } = props;
    return (
        <a className={styles.link} href={href}>
            <button onClick={handleClick} className={styles.button}>{title}</button>
        </a>
    );
};

export default Button;
