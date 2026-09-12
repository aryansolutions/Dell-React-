    import { useState } from "react";
    import "./ChatAssistant.css";

    const API_URL =
        import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";


    function ChatAssistant({ onSelectProduct })  {

        const [open, setOpen] = useState(false);
        const [message, setMessage] = useState("");
        const [messages, setMessages] = useState([
            {
                role: "assistant",
                text: "Hi! I'm your Dell AI shopping assistant. What are you looking for?"
            }
        ]);

        const [loading, setLoading] = useState(false);


        async function sendMessage(e) {

            e.preventDefault();

            const text = message.trim();

            if (!text || loading) return;


            setMessages(prev => [
                ...prev,
                {
                    role: "user",
                    text: text
                }
            ]);

            setMessage("");
            setLoading(true);


            try {
                const res = await fetch(`${API_URL}/rag-chat`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        message: text,
                    }),
                });

                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }

                const data = await res.json();

                setMessages(prev => [
                    ...prev,
                    {
                        role: "assistant",
                        text: data.response,
                        products: data.products || [],
                    },
                ]);
            } catch (err) {
                console.error("RAG CHAT ERROR:", err);

                setMessages(prev => [
                    ...prev,
                    {
                        role: "assistant",
                        text: "I couldn't reach the AI service.",
                    },
                ]);
            }

            finally {
                setLoading(false);
            }
        }


        return (
            <>

                {/* Floating button */}

                <button
                    className="aiButton"
                    onClick={() => setOpen(!open)}
                >
                    {open ? "×" : "AI"}
                </button>


                {/* Chat window */}

                {open &&

                    <div className="chatBox">


                        <div className="chatHeader">

                            <div>
                                <h3>Dell AI Assistant</h3>
                                <span>AI-powered product recommendations</span>
                            </div>

                            <button
                                onClick={() => setOpen(false)}
                            >
                                ×
                            </button>

                        </div>


                        <div className="chatMessages">

                            {messages.map((msg, index) => (

                                <div
                                    key={index}
                                    className={`chatMessage ${msg.role}`}
                                >

                                    <div className="bubble">

                                        {msg.text}

                                    </div>


                                    {/* Retrieved products */}

                                    {msg.products?.length > 0 &&

                                        <div className="recommendedProducts">

                                            {msg.products.map(product => (

                                                <div
                                                    className="recommendedCard"
                                                    key={product.id}
                                                >

                                                    <span>
                                                        Recommended
                                                    </span>

                                                    <h4>
                                                        {product.model || product.title}
                                                    </h4>

                                                    <p>
                                                        {product.description}
                                                    </p>

                                                    <b>
                                                        {product.price}
                                                    </b>

                                                    <button
                                                        className="viewProduct"
                                                        onClick={() => {
                                                            onSelectProduct(product.id);
                                                            setOpen(false);
                                                        }}
                                                    >
                                                        VIEW PRODUCT
                                                    </button>

                                                </div>

                                            ))}

                                        </div>

                                    }

                                </div>

                            ))}


                            {loading &&

                                <div className="chatMessage assistant">

                                    <div className="bubble thinking">
                                        Thinking...
                                    </div>

                                </div>

                            }

                        </div>


                        <form
                            className="chatInput"
                            onSubmit={sendMessage}
                        >

                            <input
                                type="text"
                                placeholder="Ask about Dell products..."
                                value={message}
                                onChange={
                                    e => setMessage(e.target.value)
                                }
                            />

                            <button
                                type="submit"
                                disabled={loading}
                            >
                                ➤
                            </button>

                        </form>


                    </div>

                }

            </>
        );
    }


    export default ChatAssistant;